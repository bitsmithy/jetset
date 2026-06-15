"""Tests for geospatial utility functions."""

from jetset.models import Position


class TestBearing:
    def test_north_to_south(self) -> None:
        from jetset.geo import bearing

        result = bearing(Position(0.0, 0.0), Position(-10.0, 0.0))
        assert result == 180.0

    def test_east_to_west(self) -> None:
        from jetset.geo import bearing

        result = bearing(Position(0.0, 0.0), Position(0.0, -10.0))
        assert result == 270.0

    def test_iah_to_bog(self) -> None:
        from jetset.geo import bearing

        result = bearing(Position(29.99, -95.34), Position(4.70, -74.15))
        assert round(result) == 138


class TestDistance:
    def test_iah_to_bog(self) -> None:
        from jetset.geo import distance

        result = distance(Position(29.99, -95.34), Position(4.70, -74.15))
        assert round(result) == 1936

    def test_zero_distance(self) -> None:
        from jetset.geo import distance

        result = distance(Position(29.99, -95.34), Position(29.99, -95.34))
        assert result == 0.0


class TestCrossTrackDistance:
    def test_aircraft_at_origin_zero(self) -> None:
        from jetset.geo import cross_track_distance

        origin = Position(29.99, -95.34)
        dest = Position(4.70, -74.15)
        xtd = cross_track_distance(origin, dest, origin)
        assert round(xtd) == 0

    def test_aircraft_near_iah_is_off_phx_sfo(self) -> None:
        from jetset.geo import cross_track_distance

        phx = Position(33.43, -112.02)
        sfo = Position(37.62, -122.38)
        iah = Position(29.99, -95.34)
        xtd = cross_track_distance(phx, sfo, iah)
        assert 250 < xtd < 350
