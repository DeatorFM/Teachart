from PyQt6.QtGui import QColor, QPalette, QRgba64

# base


def make_palette(color_def: dict[str, QRgba64]) -> QPalette:
    palette = QPalette()
    palette.setColor(
        QPalette.ColorRole.WindowText,
        QColor.fromRgba64(color_def.get('<c k="foreground:base"/>')),
    )
    palette.setColor(
        QPalette.ColorRole.Button,
        QColor.fromRgba64(color_def.get('<c k="treeSectionHeader.background"/>')),
    )
    palette.setColor(
        QPalette.ColorRole.ButtonText,
        QColor.fromRgba64(color_def.get('<c k="primary:base"/>')),
    )
    palette.setColor(
        QPalette.ColorRole.Base,
        QColor.fromRgba64(color_def.get('<c k="background:base"/>')),
    )
    palette.setColor(
        QPalette.ColorRole.Window,
        QColor.fromRgba64(color_def.get('<c k="background:base"/>')),
    )
    palette.setColor(
        QPalette.ColorRole.Highlight,
        QColor.fromRgba64(color_def.get('<c k="primary:base"/>')),
    )
    palette.setColor(
        QPalette.ColorRole.HighlightedText,
        QColor.fromRgba64(color_def.get('<c k="background:base"/>')),
    )
    palette.setColor(
        QPalette.ColorRole.AlternateBase,
        QColor.fromRgba64(color_def.get('<c k="list.alternateBackground"/>')),
    )
    palette.setColor(
        QPalette.ColorRole.ToolTipBase,
        QColor.fromRgba64(color_def.get('<c k="background:base" state="popup"/>')),
    )
    palette.setColor(
        QPalette.ColorRole.ToolTipText,
        QColor.fromRgba64(color_def.get('<c k="foreground:base"/>')),
    )
    if hasattr(QPalette.ColorRole, "Foreground"):
        palette.setColor(
            QPalette.ColorRole.Foreground,  # type: ignore
            QColor.fromRgba64(color_def.get('<c k="foreground:base"/>')),
        )

    palette.setColor(
        QPalette.ColorRole.Light,
        QColor.fromRgba64(color_def.get('<c k="border:base"/>')),
    )
    palette.setColor(
        QPalette.ColorRole.Midlight,
        QColor.fromRgba64(color_def.get('<c k="border:base"/>')),
    )
    palette.setColor(
        QPalette.ColorRole.Dark,
        QColor.fromRgba64(color_def.get('<c k="background:base"/>')),
    )
    palette.setColor(
        QPalette.ColorRole.Mid, QColor.fromRgba64(color_def.get('<c k="border:base"/>'))
    )
    palette.setColor(
        QPalette.ColorRole.Shadow,
        QColor.fromRgba64(color_def.get('<c k="border:base"/>')),
    )

    # disabled
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        QColor.fromRgba64(color_def.get('<c k="foreground:base" state="disabled"/>')),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor.fromRgba64(color_def.get('<c k="foreground:base" state="disabled"/>')),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Highlight,
        QColor.fromRgba64(
            color_def.get(
                '<c k="foreground:base" state="disabledSelectionBackground"/>'
            )
        ),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.HighlightedText,
        QColor.fromRgba64(color_def.get('<c k="foreground:base" state="disabled"/>')),
    )

    # inactive
    palette.setColor(
        QPalette.ColorGroup.Inactive,
        QPalette.ColorRole.Highlight,
        QColor.fromRgba64(
            color_def.get(
                '<c k="primary:base" state="list.inactiveSelectionBackground"/>'
            )
        ),
    )
    palette.setColor(
        QPalette.ColorGroup.Inactive,
        QPalette.ColorRole.HighlightedText,
        QColor.fromRgba64(color_def.get('<c k="foreground:base"/>')),
    )

    palette.setColor(
        QPalette.ColorRole.Text,
        QColor.fromRgba64(color_def.get('<c k="foreground:base" state="icon"/>')),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Text,
        QColor.fromRgba64(color_def.get('<c k="foreground:base" state="disabled"/>')),
    )
    palette.setColor(
        QPalette.ColorRole.Link,
        QColor.fromRgba64(color_def.get('<c k="primary:base"/>')),
    )
    palette.setColor(
        QPalette.ColorRole.LinkVisited,
        QColor.fromRgba64(color_def.get('<c k="linkVisited"/>')),
    )
    if hasattr(QPalette.ColorRole, "PlaceholderText"):
        palette.setColor(
            QPalette.ColorRole.PlaceholderText,
            QColor.fromRgba64(
                color_def.get('<c k="foreground:base" state="input.placeholder"/>')
            ),
        )

    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Link,
        QColor.fromRgba64(
            color_def.get(
                '<c k="foreground:base" state="disabledSelectionBackground"/>'
            )
        ),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.LinkVisited,
        QColor.fromRgba64(color_def.get('<c k="foreground:base" state="disabled"/>')),
    )

    return palette
