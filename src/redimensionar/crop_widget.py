import io
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QColor, QPixmap, QImage, QWheelEvent, QCursor, QPainterPath
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PIL import Image


class CropWidget(QWidget):
    coords_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pil = None
        self._zoom = 1.0
        self._pan = QPoint(0, 0)
        self._dragging = False
        self._drag_target = None
        self._drag_start = QPoint(0, 0)
        self._crop_rect = QRect(0, 0, 200, 200)
        self._rect_start = QPoint(0, 0)
        self._pan_start = QPoint(0, 0)
        self._sobre_corte = False
        self._resize_target = None
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)

    def set_image(self, pil_img: Image.Image):
        self._pil = pil_img.copy()
        self._zoom = 1.0
        self._pan = QPoint(0, 0)
        lado = min(pil_img.width, pil_img.height)
        self._crop_rect = QRect(0, 0, lado, lado)
        if pil_img.width > pil_img.height:
            self._crop_rect.moveLeft((pil_img.width - lado) // 2)
        self._zoom_fit()
        self.update()

    def _zoom_fit(self):
        if self._pil is None:
            return
        mw = max(self.width() - 20, 10)
        mh = max(self.height() - 20, 10)
        zx = mw / self._pil.width
        zy = mh / self._pil.height
        self._zoom = min(zx, zy, 2.0)
        self._pan = QPoint(
            (self.width() - int(self._pil.width * self._zoom)) // 2,
            (self.height() - int(self._pil.height * self._zoom)) // 2,
        )

    def zoom_in(self):
        self._apply_zoom(1.3)

    def zoom_out(self):
        self._apply_zoom(1.0 / 1.3)

    def zoom_fit(self):
        self._zoom_fit()
        self.update()

    def _apply_zoom(self, factor):
        if self._pil is None:
            return
        cx = self.width() // 2
        cy = self.height() // 2
        ix = (cx - self._pan.x()) / self._zoom if self._zoom > 0 else 0
        iy = (cy - self._pan.y()) / self._zoom if self._zoom > 0 else 0
        self._zoom = max(0.05, min(self._zoom * factor, 20.0))
        self._pan = QPoint(int(cx - ix * self._zoom), int(cy - iy * self._zoom))
        self.update()

    def crop_coords_pil(self):
        if self._pil is None:
            return None, None, None
        ix = self._crop_rect.x()
        iy = self._crop_rect.y()
        lado = self._crop_rect.width()
        w, h = self._pil.width, self._pil.height
        lado = min(lado, w, h)
        ix = max(0, min(ix, w - lado))
        iy = max(0, min(iy, h - lado))
        return ix, iy, lado

    def set_crop_coords(self, left, top, lado=None):
        if self._pil:
            w, h = self._pil.width, self._pil.height
            if lado is not None:
                lado = min(lado, w, h)
                left = max(0, min(left, w - lado))
                top = max(0, min(top, h - lado))
                self._crop_rect = QRect(left, top, lado, lado)
            else:
                lado = self._crop_rect.width()
                left = max(0, min(left, w - lado))
                top = max(0, min(top, h - lado))
                self._crop_rect.moveTopLeft(QPoint(left, top))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pil is not None:
            self._zoom_fit()

    def wheelEvent(self, event: QWheelEvent):
        if self._pil is None:
            return
        ang = event.angleDelta().y()
        mx, my = event.position().x(), event.position().y()
        ix = (mx - self._pan.x()) / self._zoom if self._zoom > 0 else 0
        iy = (my - self._pan.y()) / self._zoom if self._zoom > 0 else 0
        self._zoom = max(0.05, min(self._zoom * (1.15 if ang > 0 else 1.0 / 1.15), 20.0))
        self._pan = QPoint(int(mx - ix * self._zoom), int(my - iy * self._zoom))
        self.update()

    def _crop_screen_rect(self):
        if self._pil is None:
            return QRect()
        z = self._zoom
        px, py = self._pan.x(), self._pan.y()
        cr = self._crop_rect
        return QRect(
            px + int(cr.x() * z), py + int(cr.y() * z),
            max(1, int(cr.width() * z)), max(1, int(cr.height() * z)),
        )

    def _handle_at(self, pos):
        cr = self._crop_screen_rect()
        margin = 8
        corners = {
            "tl": cr.topLeft(), "tr": cr.topRight(),
            "bl": cr.bottomLeft(), "br": cr.bottomRight(),
        }
        for name, pt in corners.items():
            if abs(pos.x() - pt.x()) <= margin and abs(pos.y() - pt.y()) <= margin:
                return name
        return None

    def _cursor_para_handle(self, handle):
        return {
            "tl": Qt.SizeFDiagCursor, "br": Qt.SizeFDiagCursor,
            "tr": Qt.SizeBDiagCursor, "bl": Qt.SizeBDiagCursor,
        }.get(handle, Qt.ArrowCursor)

    def mouseMoveEvent(self, event):
        if self._dragging:
            dx = event.pos().x() - self._drag_start.x()
            dy = event.pos().y() - self._drag_start.y()

            if self._drag_target == "resize":
                self._resize_para(event.pos())
                return

            if self._drag_target == "crop":
                z = self._zoom
                if z == 0:
                    return
                novo_x = self._rect_start.x() + int(dx / z)
                novo_y = self._rect_start.y() + int(dy / z)
                lado = self._crop_rect.width()
                max_x = self._pil.width - lado if self._pil else 0
                max_y = self._pil.height - lado if self._pil else 0
                self._crop_rect.moveTo(max(0, min(novo_x, max_x)), max(0, min(novo_y, max_y)))
                self.coords_changed.emit()
                self.update()
                return

            elif self._drag_target == "pan":
                self._pan = QPoint(self._pan_start.x() + dx, self._pan_start.y() + dy)
                self.update()
                return

        if self._pil is None:
            return

        handle = self._handle_at(event.pos())
        if handle:
            self.setCursor(QCursor(self._cursor_para_handle(handle)))
            self._sobre_corte = False
            return

        cr = self._crop_screen_rect()
        margin = 6
        hit = QRect(cr.x() - margin, cr.y() - margin,
                    cr.width() + margin * 2, cr.height() + margin * 2)
        on_crop = hit.contains(event.pos())
        if on_crop != self._sobre_corte:
            self._sobre_corte = on_crop
            self.setCursor(QCursor(Qt.SizeAllCursor) if on_crop else QCursor(Qt.ArrowCursor))

    def _resize_para(self, pos):
        if not self._pil or self._zoom == 0:
            return
        z = self._zoom
        mx = (pos.x() - self._pan.x()) / z
        my = (pos.y() - self._pan.y()) / z
        rx, ry = self._rect_start.x(), self._rect_start.y()
        lado = self._crop_rect.width()
        target = self._resize_target

        fx, fy = {
            "br": (rx, ry),
            "bl": (rx + lado, ry),
            "tr": (rx, ry + lado),
            "tl": (rx + lado, ry + lado),
        }[target]

        size = max(10, int(abs(mx - fx) + 0.5), int(abs(my - fy) + 0.5))

        left, top = {
            "br": (fx, fy),
            "bl": (fx - size, fy),
            "tr": (fx, fy - size),
            "tl": (fx - size, fy - size),
        }[target]

        left = max(0, min(int(left), self._pil.width - size))
        top = max(0, min(int(top), self._pil.height - size))
        self._crop_rect = QRect(left, top, size, size)
        self.coords_changed.emit()
        self.update()

    def mousePressEvent(self, event):
        if self._pil is None:
            return
        handle = self._handle_at(event.pos())
        if handle:
            self._dragging = True
            self._drag_target = "resize"
            self._resize_target = handle
            self._drag_start = event.pos()
            self._rect_start = QPoint(self._crop_rect.x(), self._crop_rect.y())
            return
        if self._sobre_corte:
            self._dragging = True
            self._drag_target = "crop"
            self._drag_start = event.pos()
            self._rect_start = QPoint(self._crop_rect.x(), self._crop_rect.y())
        else:
            self._dragging = True
            self._drag_target = "pan"
            self._drag_start = event.pos()
            self._pan_start = QPoint(self._pan.x(), self._pan.y())

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._drag_target = None
        self._resize_target = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if self._pil is None:
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 8, 8)
            painter.setClipPath(path)
            painter.fillPath(path, QColor("#E8E8EE"))
            painter.setPen(QPen(QColor("#94A3B8"), 1))
            painter.drawRoundedRect(0, 0, self.width() - 1, self.height() - 1, 8, 8)
            painter.setClipping(False)
            painter.setPen(QColor("#CCC"))
            font = painter.font()
            font.setPointSize(36)
            painter.setFont(font)
            cy = self.height() // 2
            painter.drawText(QRect(0, cy - 50, self.width(), 60), Qt.AlignCenter, "🖼")
            font.setPointSize(13)
            painter.setFont(font)
            painter.setPen(QColor("#AAA"))
            painter.drawText(QRect(0, cy + 10, self.width(), 30), Qt.AlignCenter, "Selecione imagens para começar")
            return

        z = self._zoom
        pw = int(self._pil.width * z)
        ph = int(self._pil.height * z)
        px, py = self._pan.x(), self._pan.y()

        qpix = self._pil_to_qpixmap(self._pil)
        scaled = qpix.scaled(pw, ph, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(px, py, scaled)

        painter.fillRect(0, 0, self.width(), py, QColor(0, 0, 0, 140))
        painter.fillRect(0, py + ph, self.width(), self.height(), QColor(0, 0, 0, 140))
        painter.fillRect(0, py, px, ph, QColor(0, 0, 0, 140))
        painter.fillRect(px + pw, py, self.width(), ph, QColor(0, 0, 0, 140))

        cr = self._crop_rect
        rx = px + int(cr.x() * z)
        ry = py + int(cr.y() * z)
        rw = max(1, int(cr.width() * z))
        rh = max(1, int(cr.height() * z))

        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setPen(QPen(QColor("white"), 3))
        painter.drawRect(rx, ry, rw, rh)

        metade = rw // 2
        painter.setPen(QPen(QColor(255, 255, 255, 120), 1, Qt.DashLine))
        painter.drawLine(rx + metade, ry, rx + metade, ry + rh)
        painter.drawLine(rx, ry + metade, rx + rw, ry + metade)

        handle = 8
        painter.setBrush(QColor("white"))
        painter.setPen(QPen(QColor("#333"), 1))
        for hx, hy in [(rx, ry), (rx + rw, ry), (rx, ry + rh), (rx + rw, ry + rh)]:
            painter.drawRect(hx - handle // 2, hy - handle // 2, handle, handle)

    def _pil_to_qpixmap(self, pil_img):
        buf = io.BytesIO()
        if pil_img.mode == "RGBA":
            pil_img.save(buf, format="PNG")
            qimg = QImage()
            qimg.loadFromData(buf.getvalue(), "PNG")
        else:
            img_rgb = pil_img.convert("RGB")
            img_rgb.save(buf, format="JPEG")
            qimg = QImage()
            qimg.loadFromData(buf.getvalue(), "JPG")
        return QPixmap.fromImage(qimg)
