import logging
import threading
import time
from pathlib import Path
from typing import NamedTuple

from RGBMatrixEmulator.emulation.canvas import Canvas
from RGBMatrixEmulator.emulation.matrix import RGBMatrix

from jetset.config import AppConfig
from jetset.fetcher import AirLabsAdapter, FlightAPI
from jetset.models import Flight, FlightBuffer
from jetset.renderer import render_flight_card, render_loading

logger = logging.getLogger(__name__)


class App:
    # How often the background fetch thread wakes to check if a refresh is due.
    _FETCH_POLL_SECONDS = 1.0
    # Display rotates a sliding window of this many flights; 4 metric pages each.
    WINDOW_SIZE = 5
    PAGES_PER_FLIGHT = 4

    class Frame(NamedTuple):
        flight: Flight
        metric_page: int

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.logo_dir = Path(config.logo_dir)
        self.buffer = FlightBuffer()
        self.frame = 0
        self.last_fetch: float | None = None
        self.adapter: FlightAPI = _create_adapter(config)
        # Fetching runs on a background thread so the render loop never blocks
        # on the (multi-second) network round-trips. _lock guards the shared
        # buffer; _stop signals the fetch thread to exit.
        self._lock = threading.Lock()
        self._stop = threading.Event()

    def _should_fetch(self) -> bool:
        now = time.time()
        if not self.last_fetch or now - self.last_fetch >= self.config.refresh:
            return True
        else:
            return False

    def _fetch(self):
        # One AirLabs fetch captures all nearby flights (with routes + metrics);
        # replace the buffer wholesale. The display then slides a window across
        # them until the next refresh. Network happens outside the lock.
        flights = self.adapter.nearby_flights(
            self.config.home_lat, self.config.home_lon, self.config.range
        )

        with self._lock:
            self.buffer.set_all(flights)

        self.last_fetch = time.time()

    def _safe_fetch(self) -> None:
        """Run a fetch cycle, swallowing unexpected errors.

        nearby_flights/refresh_flight already handle expected network and parse
        errors; this is the last line of defense so an unforeseen failure logs
        and the display keeps showing existing flights instead of crashing the
        loop. last_fetch is advanced so a persistent failure backs off to the
        normal refresh interval rather than retrying every frame.
        """
        try:
            self._fetch()
        except Exception:
            logger.exception("Fetch cycle failed; keeping existing flights")
            self.last_fetch = time.time()

    def _fetch_loop(self) -> None:
        """Background loop: refresh flights when due until stopped.

        Runs on its own thread so the multi-second fetch never blocks the
        render loop. Polls frequently but only fetches once the refresh
        interval has elapsed.
        """
        while not self._stop.is_set():
            if self._should_fetch():
                self._safe_fetch()
            self._stop.wait(self._FETCH_POLL_SECONDS)

    def _current_frame(self) -> Frame | None:
        with self._lock:
            flights = self.buffer.flights

        n = len(flights)
        if n == 0:
            return None

        window = min(self.WINDOW_SIZE, n)
        # Slide the window across all captured flights once per refresh interval
        # so fresh flights trickle into the rotation between (infrequent) fetches.
        # The slide cadence scales with the catch size (refresh / N).
        slide_interval = self.config.refresh / n
        since = self.last_fetch if self.last_fetch is not None else time.time()
        elapsed = time.time() - since
        window_start = int(elapsed / slide_interval) % n if slide_interval else 0

        # Within the window, rotate one flight at a time through its metric pages.
        flight_in_window = (self.frame // self.PAGES_PER_FLIGHT) % window
        metric_page = self.frame % self.PAGES_PER_FLIGHT

        return self.Frame(flights[(window_start + flight_in_window) % n], metric_page)

    def _after_render(self, matrix: RGBMatrix, canvas: Canvas) -> Canvas:
        # This needs to be it's own method so that tests don't need to run the infinite loop method.
        # SwapOnVSync returns the now-offscreen buffer to draw the *next* frame into; on real
        # hardware this double-buffering is mandatory, or frames flash and tear over stale content.
        next_canvas = matrix.SwapOnVSync(canvas)
        self.frame += 1
        time.sleep(self.config.pause)
        return next_canvas

    def _render_frame(self, matrix: RGBMatrix, canvas: Canvas, frame: Frame) -> Canvas:
        flight, metric_page = frame
        render_flight_card(canvas, flight, self.logo_dir, metric_page)
        return self._after_render(matrix, canvas)

    def _render_loading(self, matrix: RGBMatrix, canvas: Canvas) -> Canvas:
        # % 4 so the "LOADING." dots keep cycling instead of freezing on
        # "LOADING" once the frame counter passes 3.
        render_loading(canvas, self.frame % self.PAGES_PER_FLIGHT)
        return self._after_render(matrix, canvas)

    def loop(self, matrix: RGBMatrix, canvas: Canvas):
        # Fetching runs on a background thread; this loop only renders, so the
        # display keeps cycling smoothly while a fetch is in flight.
        canvas = self._render_loading(matrix, canvas)

        fetch_thread = threading.Thread(
            target=self._fetch_loop, name="jetset-fetch", daemon=True
        )
        fetch_thread.start()

        try:
            while True:
                if frame := self._current_frame():
                    canvas = self._render_frame(matrix, canvas, frame)
                else:
                    canvas = self._render_loading(matrix, canvas)
        except KeyboardInterrupt:
            self._stop.set()
            canvas.Clear()
            matrix.SwapOnVSync(canvas)


def _create_adapter(config: AppConfig):
    if config.api_source == "airlabs":
        return AirLabsAdapter()
    raise ValueError(f"Unknown api_source: {config.api_source}")
