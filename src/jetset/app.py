import logging
import threading
import time
from pathlib import Path
from typing import NamedTuple

from jetset.backend import build_matrix
from jetset.config import AppConfig
from jetset.fetcher import AirLabsAdapter, FlightAPI
from jetset.models import Flight, FlightBuffer
from jetset.renderer import Renderer

logger = logging.getLogger(__name__)


class App:
    # How often the background fetch thread wakes to check if a refresh is due.
    _FETCH_POLL_SECONDS = 1.0
    # Display rotates a sliding window of this many flights; 4 metric pages each.
    WINDOW_SIZE = 5
    PAGES_PER_FLIGHT = 5

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
        # Show a sliding window of flights, one at a time. Each flight gets
        # cycles_per_flight * PAGES_PER_FLIGHT frames (e.g. 1 cycle = all 4
        # metric pages once) before advancing to the next. After every flight
        # in the current window has been shown, slide the window by 1 so fresh
        # flights trickle in.
        frames_per_flight = self.PAGES_PER_FLIGHT * self.config.cycles_per_flight
        frames_per_window_cycle = frames_per_flight * window
        cycle = self.frame // frames_per_window_cycle
        window_start = cycle % max(1, n - window + 1) if n else 0
        flight_in_window = (self.frame % frames_per_window_cycle) // frames_per_flight
        metric_page = self.frame % self.PAGES_PER_FLIGHT

        return self.Frame(flights[(window_start + flight_in_window) % n], metric_page)

    def loop(self) -> None:
        matrix = build_matrix()

        # Fetching runs on a background thread; this loop only renders, so the
        # display keeps cycling smoothly while a fetch is in flight. The Renderer
        # owns the double-buffered canvas; present() does the VSync swap.
        renderer = Renderer(matrix, self.logo_dir)

        fetch_thread = threading.Thread(target=self._fetch_loop, name="jetset-fetch", daemon=True)
        fetch_thread.start()

        try:
            while True:
                if frame := self._current_frame():
                    renderer.flight_card(frame.flight, frame.metric_page)
                else:
                    # % 4 so the "LOADING." dots keep cycling instead of freezing.
                    renderer.loading(self.frame % self.PAGES_PER_FLIGHT)
                renderer.present()
                self.frame += 1
                time.sleep(self.config.pause)
        except KeyboardInterrupt:
            self._stop.set()
            renderer.clear()


def _create_adapter(config: AppConfig):
    if config.api_source == "airlabs":
        return AirLabsAdapter()
    raise ValueError(f"Unknown api_source: {config.api_source}")
