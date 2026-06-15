import time
from typing import NamedTuple

from RGBMatrixEmulator.emulation.canvas import Canvas
from RGBMatrixEmulator.emulation.matrix import RGBMatrix

from jetset.config import AppConfig
from jetset.fetcher import AdsbLolAdapter, FlightAPI
from jetset.models import Flight, FlightBuffer
from jetset.renderer import render_flight_card, render_loading


class App:
    class Frame(NamedTuple):
        flight: Flight
        metric_page: int

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.buffer = FlightBuffer()
        self.frame = 0
        self.last_fetch: float | None = None
        self.adapter: FlightAPI = _create_adapter(config)

    def _should_fetch(self) -> bool:
        now = time.time()
        if not self.last_fetch or now - self.last_fetch >= self.config.refresh:
            return True
        else:
            return False

    def _fetch(self):
        flights = self.adapter.nearby_flights(
            self.config.home_lat, self.config.home_lon, self.config.range
        )

        live_callsigns = {f.callsign for f in flights}

        for f in flights:
            self.buffer.push(f)

        for existing in self.buffer.flights:
            if existing.callsign not in live_callsigns:
                self.buffer.replace(existing.callsign, self.adapter.refresh_flight(existing))

        self.last_fetch = time.time()

    def _current_frame(self) -> Frame | None:
        if not self.buffer.flights:
            return None

        idx = self.frame // 4 % len(self.buffer.flights)
        metric_page = self.frame % 4

        return self.Frame(self.buffer.flights[idx], metric_page)

    def _after_render(self, matrix: RGBMatrix, canvas: Canvas):
        # This needs to be it's own method so that tests don't need to run the infinite loop method
        matrix.SwapOnVSync(canvas)
        self.frame += 1
        time.sleep(self.config.pause)

    def _render_frame(self, matrix: RGBMatrix, canvas: Canvas, frame: Frame):
        flight, metric_page = frame
        render_flight_card(canvas, flight, metric_page)
        self._after_render(matrix, canvas)

    def _render_loading(self, matrix: RGBMatrix, canvas: Canvas):
        render_loading(canvas, self.frame)
        self._after_render(matrix, canvas)

    def loop(self, matrix: RGBMatrix, canvas: Canvas):
        try:
            while True:
                if self._should_fetch():
                    self._fetch()

                if frame := self._current_frame():
                    self._render_frame(matrix, canvas, frame)
                else:
                    self._render_loading(matrix, canvas)
        except KeyboardInterrupt:
            canvas.Clear()
            matrix.SwapOnVSync(canvas)


def _create_adapter(config: AppConfig):
    if config.api_source == "adsblol":
        return AdsbLolAdapter()
    raise ValueError(f"Unknown api_source: {config.api_source}")
