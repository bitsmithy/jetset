"""Tests for the LED matrix backend selector."""


class TestBackendContract:
    def test_exposes_matrix_classes(self) -> None:
        from jetset import backend

        assert hasattr(backend, "RGBMatrix")
        assert hasattr(backend, "RGBMatrixOptions")

    def test_exposes_graphics_drawing_api(self) -> None:
        from jetset import backend

        assert hasattr(backend.graphics, "Font")
        assert hasattr(backend.graphics, "Color")
        assert hasattr(backend.graphics, "DrawText")

    def test_reports_hardware_flag_as_bool(self) -> None:
        from jetset import backend

        assert isinstance(backend.IS_HARDWARE, bool)


class TestRendererBackendConsistency:
    def test_renderer_draws_with_the_active_backend_graphics(self) -> None:
        # The garble bug was the renderer using the emulator's graphics engine
        # to draw onto a hardware canvas. Renderer and matrix must share one
        # backend, or glyphs and buffering won't match the canvas.
        from jetset import backend, renderer

        assert renderer.graphics is backend.graphics
