def fromStyle(stylesheet: str) -> str:
    with open(f"resources/stylesheets/{stylesheet}.qss", "r", encoding="utf-8") as f:
        return f.read()
    
from PyQt6.QtGui import QColor

def convertColors(colors: list[str]) -> list[QColor]:
    converted = []
    for color in colors:
        converted.append(QColor().fromString(color))
    return converted

def paintIcon(svgpath: str, color: QColor) -> "QPixmap":
    from PyQt6.QtGui import QPixmap, QPainter
    img = QPixmap(svgpath)
    painter = QPainter(img)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(img.rect(), color)
    painter.end()
    return img