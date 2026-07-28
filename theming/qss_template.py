"""Template stylesheet adapted from PyQtDarkTheme by 5yutan5"""

TEMPLATE_STYLESHEET = """
QWidget {
    background: <t><c k="background:base" /></t>;
    color: <t><c k="foreground:base"/></t>;
    selection-color:<t><c k="foreground:base"/></t>;
    selection-background-color:<t><c k="primary:base" state="selection.background"/></t>
    }

QWidget:disabled {
    color:<t><c k="foreground:base" state="disabled"/></t>;
    selection-background-color:<t><c k="foreground:base" state="disabledSelectionBackground"/></t>;
    selection-color:<t><c k="foreground:base" state="disabled"/></t>
    }
    
QWidget:focus {
    outline:none
    }
    
QCheckBox:!window,

QRadioButton:!window,

QPushButton:!window,

QLabel:!window,

QLCDNumber:!window {
    background:transparent
    }

QMdiSubWindow > QCheckBox:!window,
QMdiSubWindow > QRadioButton:!window,
QMdiSubWindow > QPushButton:!window,
QMdiSubWindow > QLabel:!window,
QMdiSubWindow > QLCDNumber:!window {
    background: <t><c k="background:base"/></t>
    }
    
QMainWindow::separator {
    width:4px;
    height:4px;
    background: <t><c k="border:base"/></t>
    }
    
QMainWindow::separator:hover,
QMainWindow::separator:pressed {
    background: <t><c k="primary:base"/></t>
    }
    
QToolTip {
    background: <t><c k="background:base" state="popup"/></t>;
    color: <t><c k="foreground:base"/></t>
    }
    
QSizeGrip {
    width:0;
    height:0;
    image:none
    }

QStatusBar 
    background: <t><c k="statusBar.background"/></t>
    }
    
QStatusBar::item {
    border:none
    }

QStatusBar QWidget {
    background:transparent;
    padding:3px;
    border-radius:round 4px
    }
    
QStatusBar > .QSizeGrip {
    padding:0
    }
    
QStatusBar QWidget:hover {
    background: <t><c k="statusBarItem.hoverBackground"/></t>
    }
    
QStatusBar QWidget:pressed,QStatusBar QWidget:checked {
    background:<t><c k="statusBarItem.activeBackground"/></t>
    }
    
QCheckBox,QRadioButton {
    border-top:2px solid transparent;
    border-bottom:2px solid transparent
    }
    
QCheckBox:hover,QRadioButton:hover {
    border-bottom:2px solid <t><c k="primary:base"/></t>
    }
    
QGroupBox {
    font-weight:bold;
    margin-top:8px;
    padding:2px 1px 1px 1px;
    border-radius:round 4px;
    border:1px solid <t><c k="border:base"/></t>
    }
    
QGroupBox::title {
    subcontrol-origin:margin;
    subcontrol-position:top left;
    left:7px;
    margin:0 2px 0 3px
    }
    
QGroupBox:flat {
    border-color:transparent
    }

QMenuBar {
    padding:2px;
    border-bottom:1px solid <t><c k="border:base"/></t>;
    background: <t><c k="background:base"/></t>
    }
    
QMenuBar::item {
    background:transparent;
    padding:4px
    }
    
QMenuBar::item:selected {
    padding:4px;
    border-radius: 4px;
    background: <t><c k="menubar.selectionBackground"/></t>
    }
    
QMenuBar::item:pressed {
    padding:4px;
    margin-bottom:0;
    padding-bottom:0
    }
    
QToolBar {
    padding:1px;
    font-weight:bold;
    spacing:2px;
    margin:1px;
    background: <t><c k="toolbar.background"/></t>;
    border-style:none
    }
    
QToolBar::handle:horizontal {
    width:20px;
    image: <t><img><c k="foreground:base" state="icon"/><url id="drag_indicator"/></img></t>
    }
    
QToolBar::handle:vertical {
    height:20px;
    image: <t><img><c k="foreground:base" state="icon"/><url id="drag_indicator" rotate="90"/></img></t>
    }
    
QToolBar::handle:horizontal:disabled {
    image: <t><img><c k="foreground:base" state="disabled"/><url id="drag_indicator"/></img></t>
    }
    
QToolBar::handle:vertical:disabled {
    image: <t><img><c k="foreground:base" state="disabled"/><url id="drag_indicator" rotate="90"/></img></t>
    }
    
QToolBar::separator {
    background: <t><c k="border:base"/></t>;
    }
    
QToolBar::separator:horizontal {
    width:2px;
    margin:0 6px
    }
    
QToolBar::separator:vertical {
    height:2px;
    margin:6px 0
    }
    
QToolBar > QToolButton {
    background:transparent;
    padding:3px;
    border-radius: 4px
    }
    
QToolBar > QToolButton:hover,QToolBar > QToolButton::menu-button:hover {
    background: <t><c k="toolbar.hoverBackground"/></t>;
    }
    
QToolBar > QToolButton::menu-button {
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px
    }
    
QToolBar > QToolButton:pressed,QToolBar > QToolButton::menu-button:pressed:enabled,QToolBar > QToolButton:checked:enabled {
    background: <t><c k="toolbar.activeBackground"/></t>;
    }
    
QToolBar > QWidget {
    background:transparent
    }
    
QMenu {
    background: <t><c k="background:base" state="popup"/></t>;
    padding:8px 0;
    <env><if os="Darwin" value="border-radius:4px;"></env>
    }
    
QMenu::separator {
    margin:4px 0;
    height:1px;
    background: <t><c k="border:base"/></t>;
    }
    
QMenu::item {
    padding:4px 19px
    }
    
QMenu::item:selected {
    background: <t><c k="popupItem.selectionBackground"/></t>
    }
    
QMenu::icon {
    padding-left:10px;
    width:14px;
    height:14px
    }
    
QMenu::right-arrow {
    margin:2px;
    padding-left:12px;
    height:20px;
    width:20px;
    image: <t><img><c k="foreground:base" state="icon"/><url id="chevron_right"/></img></t>
    }
    
QMenu::right-arrow:disabled {
    image: <t><img><c k="foreground:base" state="disabled"/><url id="chevron_right"/></img></t>
    }
    
QScrollBar {
    background: <t><c k="scrollbar.background"/></t>;
    border-radius: 4px;
    <t><env><if value="background:transparent" os="Darwin"/></env></t>
    }
    
QScrollBar:horizontal {
    <t><env><if value="height:7px" os="Darwin"/><else value="height:14px;"/></env></t>
    }
    
QScrollBar:vertical {
    <t><env><if value="width:7px" os="Darwin"/><else value="width:14px;"/></env></t>
    }
    
QScrollBar::handle {
    background: <t><c k="scrollbarSlider.background"/></t>;
    border-radius:3px
    }
    
QScrollBar::handle:hover {
    background: <t><c k="scrollbarSlider.hoverBackground"/></t>
    }
    
QScrollBar::handle:pressed {
    background: <t><c k="scrollbarSlider.activeBackground"/></t>
    }
    
QScrollBar::handle:disabled {
    background: <t><c k="scrollbarSlider.disabledBackground"/></t>
    }
    
QScrollBar::handle:horizontal {
    min-width:8px;
    <t><env><if value="margin:5" os="Darwin"/><else value="margin:4px 14px;"/></env></t>
    }
    
QScrollBar::handle:horizontal:hover {
    <t><env><if value="margin:5" os="Darwin"/><else value="margin:2px 14px;"/></env></t>
    }
    
QScrollBar::handle:vertical {
    min-height:8px;
    <t><env><if value="margin:0px" os="Darwin"/><else version="margin:14px 4px;"/></env></t>
    }
    
QScrollBar::handle:vertical:hover {
    <t><env><if value="margin:0" os="Darwin"/><else value="margin:14px 2px;"/></env></t>
    }
    
QScrollBar::sub-page,QScrollBar::add-page {
    background:transparent
    }
    
QScrollBar::sub-line,QScrollBar::add-line {
    background:transparent;
    <t><env><if value="width:0px;height:0px" os="Darwin"/></env></t>
    }
    
QScrollBar::up-arrow:enabled {
    image: <t><img><c k="scrollbarSlider.background"/><url id="arrow_drop_up"/></img></t>
    }
    
QScrollBar::right-arrow:enabled {
    image: <t><img><c k="scrollbarSlider.background"/><url id="arrow_drop_up" rotate="90"/></img></t>
    }
    
QScrollBar::down-arrow:enabled {
    image: <t><img><c k="scrollbarSlider.background"/><url id="arrow_drop_up" rotate="180"/></img></t>
    }
    
QScrollBar::left-arrow:enabled {
    image:<t><img><c k="scrollbarSlider.background"/><url id="arrow_drop_up" rotate="270"/></img></t>
    }
    
QScrollBar::up-arrow:hover {
    image: <t><img><c k="scrollbarSlider.activeBackground"/><url id="arrow_drop_up"/></img></t>
    }
    
QScrollBar::right-arrow:hover {
    image: <t><img><c k="scrollbarSlider.activeBackground"/><url id="arrow_drop_up" rotate="90"/></img></t>
    }
    
QScrollBar::down-arrow:hover {
    image: <t><img><c k="scrollbarSlider.activeBackground"/><url id="arrow_drop_up" rotate="180"/></img></t>
    }
    
QScrollBar::left-arrow:hover {
    image: <t><img><c k="scrollbarSlider.activeBackground"/><url id="arrow_drop_up" rotate="270"/></img></t>
    }
    
QProgressBar {
    text-align:center;
    border:1px solid <t><c k="border:base"/></t>;
    border-radius:4px
    }
    
QProgressBar::chunk {
    background: <t><c k="primary:base" state="progressBar.background"/></t>;
    border-radius:3px
    }
    
QProgressBar::chunk:disabled {
    background: <t><c k="foreground:base" state="progressBar.disabledBackground"/></t>
    }
    
QPushButton {
    color: <t><c k="primary:base"/></t>;
    border:1px solid <t><c k="border:base"/></t>;
    padding:4px 8px;
    border-radius:4px
    }
    
QPushButton:flat,QPushButton:default {
    border:none;
    padding:5px 9px
    }
    
QPushButton:default {
    color:<t><c k="background:base"/></t>;
    background:<t><c k="primary:base"/></t>
    }
    
QPushButton:hover {
    background: <t><c k="primary:base" state="button.hoverBackground"/></t>
    }
    
QPushButton:pressed {
    background: <t><c k="primary:base" state="button.activeBackground"/></t>
    }
    
QPushButton:checked:enabled {
    background:<t><c k="primary:base" state="button.activeBackground"/></t>
    }
    
QPushButton:default:hover {
    background: <t><c k="primary:base" state="defaultButton.hoverBackground"/></t>
    }
    
QPushButton:default:pressed,QPushButton:default:checked {
    background:<t><c k="primary:base" state="defaultButton.activeBackground"/></t>
    }
    
QPushButton:default:disabled,QPushButton:default:checked:disabled {
    background: <t><c k="foreground:base" state="defaultButton.disabledBackground"/></t>
    }
    
QDialogButtonBox {
    dialogbuttonbox-buttons-have-icons:0
    }
    
QDialogButtonBox QPushButton {
    min-width:65px
    }
    
QToolButton {
    background:transparent;
    padding:5px;
    spacing:2px;
    border-radius:2px
    }
    
QToolButton:hover,QToolButton::menu-button:hover {
    background: <t><c k="primary:base" state="button.hoverBackground"/></t>
    }
    
QToolButton:pressed,QToolButton:checked:pressed,QToolButton::menu-button:pressed:enabled {
    background: <t><c k="primary:base" state="button.activeBackground"/></t>
    }
    
QToolButton:selected:enabled,QToolButton:checked:enabled {
    background: <t><c k="primary:base" state="button.activeBackground"/></t>
    }
    
QToolButton::menu-indicator {
    height:18px;
    width:18px;
    top:6px;
    left:3px;
    image: <t><img><c k="foreground:base" state="icon"/><url id="expand_less" rotate="180"/></img></t>
    }
    
QToolButton::menu-indicator:disabled {
    image: <t><img><c k="foreground:base" state="disabled"/><url id="expand_less" rotate="180"/></img></t>
    }
    
QToolButton::menu-arrow {
    image:unset
    }

QToolButton::menu-button {
    subcontrol-origin:margin;
    width:17px;
    border-top-right-radius:2px;
    border-bottom-right-radius:2px;
    image: <t><img><c k="foreground:base" state="icon"/><url id="expand_less" rotate="180"/></img></t>
    }
    
QToolButton::menu-button:disabled {
    image: <t><img><c k="foreground:base" state="disabled"/><url id="expand_less" rotate="180"/></img></t>
    }
    
QToolButton[popupMode=MenuButtonPopup] {
    padding-right:1px;
    margin-right:18px;
    border-top-right-radius:0;
    border-bottom-right-radius:0
    }
    
QComboBox {
    min-height:1.5em;
    padding:0 8px 0 4px;
    background:<t><c k="input.background"/></t>;
    border:1px solid <t><c k="border:base" state="input"/></t>;
    border-radius:4px
    }
    
QComboBox:focus,QComboBox:open {
    border-color:<t><c k="primary:base"/></t>
    }
    
QComboBox::drop-down {
    margin:2px 2px 2px -6px;
    border-radius:round 4
    }
    
QComboBox::drop-down:editable:hover {
    background:<t><c k="inputButton.hoverBackground"/></t>
    }
    
QComboBox::down-arrow {
    image: <t><img><c k="foreground:base" state="icon"/><url id="expand_less" rotate="180"/></img></t>
    }
    
QComboBox::down-arrow:disabled {
    image: <t><img><c k="foreground:base" state="disabled"/><url id="expand_less" rotate="180"/></img></t>
    }
    
QComboBox::down-arrow:editable:open {
    image: <t><img><c k="foreground:base" state="icon"/><url id="expand_less"/></img></t>
    }
    
QComboBox::down-arrow:editable:open:disabled {
    image: <t><img><c k="foreground:base" state="disabled"/><url id="expand_less"/></img></t>
    }
    
QComboBox::item:selected {
    border:none;
    background: <t><c k="primary:base" state="list.selectionBackground"/></t>;
    border-radius:4px
    }
    
QComboBox QListView[frameShape=NoFrame"] {
    margin:0;
    padding:4px;
    background: <t><c k="background:base" state="popup"/></t>;
    <t><env><if value="border-radius:4px" os="Darwin"/><else value="border-radius:0"/></env></t> 
    }
    
QComboBox QListView::item {
    border-radius:4px
    }
    
QSlider {
    padding:2px 0
    }
    
QSlider::groove {
    border-radius:2px
    }
    
QSlider::groove:horizontal {
    height:4px
    }
    
QSlider::groove:vertical {
    width:4px
    }
    
QSlider::sub-page:horizontal,QSlider::add-page:vertical,QSlider::handle {
    background: <t><c k="primary:base"/></t>
    }
    
QSlider::sub-page:horizontal:disabled,QSlider::add-page:vertical:disabled,QSlider::handle:disabled {
    background: <t><c k="foreground:base" state="slider.disabledBackground"/></t>
    }
    
QSlider::add-page:horizontal,QSlider::sub-page:vertical {
    background: <t><c k="foreground:base" state="sliderTrack.inactiveBackground"/></t>
    }
    
QSlider::handle:hover,QSlider::handle:pressed {
    background: <t><c k="primary:base" state="sliderHandle.activeBackground"/></t>
    }
    
QSlider::handle:horizontal {
    width:16px;
    height:8px;
    margin:-6px 0;
    border-radius:8px
    }
    
QSlider::handle:vertical {
    width:8px;
    height:16px;
    margin:0 -6px;
    border-radius:8px
    }
    
QTabWidget::pane {
    border:1px solid <t><c k="border:base"/></t>;
    border-radius:4px
    }
    
QTabBar {
    qproperty-drawBase:0
    }
    
QTabBar::close-button {
    image:<t><img><c k="foreground:base" state="icon"/><url id="close"/></img></t>
    }
    
QTabBar::close-button:hover {
    background: <t><c k="tabCloseButton.hoverBackground"/></t>;
    border-radius:4px
    }
    
QTabBar::close-button:!selected {
    image:<t><img><c k="foreground:base" state="icon.unfocused"/><url id="close"/></img></t>
    }
    
QTabBar::close-button:disabled {
    <t><img><c k="foreground:base" state="disabled"/><url id="close"/></img></t>
    }
    
QTabBar::tab {
    padding:3px;
    border-style:solid}

QTabBar::tab:hover,QTabBar::tab:selected:hover:enabled {
    background:<t><c k="tab.hoverBackground"/></t>
    }

QTabBar::tab:selected:enabled {
    color:<t><c k="primary:base"/></t>;
    background:<t><c k="tab.activeBackground"/></t>;
    border-color:<t><c k="primary:base"/></t>
    }

QTabBar::tab:selected:disabled,QTabBar::tab:only-one:selected:enabled {
    border-color:<t><c k="border:base"/></t>
    }

QTabBar::tab:top {
    border-bottom-width:2px;
    margin:3px 6px 0 0;
    border-top-left-radius:2px;
    border-top-right-radius:2px
    }

QTabBar::tab:bottom {
    border-top-width:2px;
    margin:0 6px 3px 0;
    border-bottom-left-radius:2px;
    border-bottom-right-radius:2px
    }

QTabBar::tab:left {
    border-right-width:2px;
    margin:0 0 6px 3px;
    border-top-left-radius:2px;
    border-bottom-left-radius:2px
    }

QTabBar::tab:right {
    border-left-width:2px;
    margin-bottom:6px;
    margin:0 3px 6px 0;
    border-top-right-radius:2px;
    border-bottom-right-radius:2px
    }

QTabBar::tab:top:first,QTabBar::tab:top:only-one,QTabBar::tab:bottom:first,QTabBar::tab:bottom:only-one {
    margin-left:2px
    }

QTabBar::tab:top:last,QTabBar::tab:top:only-one,QTabBar::tab:bottom:last,QTabBar::tab:bottom:only-one {
    margin-right:2px
    }

QTabBar::tab:left:first,QTabBar::tab:left:only-one,QTabBar::tab:right:first,QTabBar::tab:right:only-one {
    margin-top:2px
    }

QTabBar::tab:left:last,QTabBar::tab:left:only-one,QTabBar::tab:right:last,QTabBar::tab:right:only-one {
    margin-bottom:2px
    }

QDockWidget {
    border:1px solid <t><c k="border:base"/></t>;
    rder-radius:4px
    }

QDockWidget::title {
    padding:3px;
    spacing:4px;
    background:<t><c k="background:base" state="title"/></t>
    }

QDockWidget::close-button,QDockWidget::float-button {
    border-radius:2px
    }

QDockWidget::close-button:hover,QDockWidget::float-button:hover {
    background:<t><c k="primary:base" state="button.hoverBackground"/></t>
    }

QDockWidget::close-button:pressed,QDockWidget::float-button:pressed {
    background:<t><c k="primary:base" state="button.activeBackground"/></t>
    }

QFrame {
    border:1px solid <t><c k="border:base"/></t>;
    padding:1px;
    border-radius:4px
    }
    
.QFrame {
    padding:0
    }

    
QFrame[frameShape=NoFrame] {
    border-color:transparent;
    padding:0
    }
    
.QFrame[frameShape=NoFrame] {
    border:none
    }

QFrame[frameShape=Panel] {
    border-color:<t><c k="background:base" state="panel"/></t>;
    background:<t><c k="background:base" state="panel"/></t>
    }

QFrame[frameShape=HLine] {
    max-height:2px;
    border:none;
    background:<t><c k="border:base"/></t>
    }

QFrame[frameShape=VLine] {
    max-width:2px;
    border:none;
    background:<t><c k="border:base"/></t>
    }

QLCDNumber {
    min-width:2em;
    margin:2px
    }

QToolBox::tab {
    background:<t><c k="background:base" state="title"/></t>;
    border-bottom:2px solid <t><c k="border:base"/></t>;
    border-top-left-radius:4px;
    border-top-right-radius:4px
    }

QToolBox::tab:selected:enabled {
    border-bottom-color:<t><c k="primary:base"/></t>
    }

QSplitter::handle {
    background:<t><c k="border:base"/></t>;
    margin:1px 3px
    }

QSplitter::handle:hover {
    background:<t><c k="primary:base"/></t>
    }

QSplitter::handle:horizontal {
    width:5px;
    image:<t><img><c k="foreground:base" state="icon"/><url id="horizontal_rule" rotate="90"/></img></t>
    }

QSplitter::handle:horizontal:disabled {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="horizontal_rule" rotate="90"/></img></t>
    }

QSplitter::handle:vertical {
    height:5px;
    image:<t><img><c k="foreground:base" state="icon"/><url id="horizontal_rule"/></img></t>
    }

QSplitter::handle:vertical:disabled {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="horizontal_rule"/></img></t>
    }

QSplitterHandle::item:hover {
    }

QAbstractScrollArea {
    margin:1px
    }

QAbstractScrollArea::corner {
    background:transparent
    }

QAbstractScrollArea > .QWidget {
    background:transparent
    }

QAbstractScrollArea > .QWidget > .QWidget {
    background:transparent
    }

QMdiArea {
    qproperty-background:<t><c k="background:base" state="panel"/></t>;
    border-radius:0
    }

QMdiSubWindow {
    background:<t><c k="background:base"/></t>;
    border:1px solid;
    padding:0 3px
    }

QMdiSubWindow > QWidget {
    border:1px solid <t><c k="border:base"/></t>
    }

QTextEdit, QPlainTextEdit {
    background:<t><c k="background:base" state="textarea"/></t>
    }

QTextEdit:focus,QTextEdit:selected,QPlainTextEdit:focus,QPlainTextEdit:selected {
    border:1px solid <t><c k="primary:base"/></t>;
    selection-background-color:<t><c k="primary:base" state="textarea.selectionBackground"/></t>
    }

QTextEdit:!focus,QPlainTextEdit:!focus {
    selection-background-color:<t><c k="textarea.inactiveSelectionBackground"/></t>
    }


QAbstractItemView {
    padding:0;
    alternate-background-color:transparent;
    selection-background-color:transparent
    }

QAbstractItemView:disabled {
    selection-background-color:transparent
    }

QAbstractItemView::item:alternate,QAbstractItemView::branch:alternate {
    background:<t><c k="list.alternateBackground"/></t>
    }

QAbstractItemView::item:selected,QAbstractItemView::branch:selected {
    background:<t><c k="primary:base" state="list.selectionBackground"/></t>
    }

QAbstractItemView::item:selected:!active,QAbstractItemView::branch:selected:!active {
    background:<t><c k="primary:base" state="list.inactiveSelectionBackground"/></t>
    }

QAbstractItemView QLineEdit,QAbstractItemView QAbstractSpinBox,QAbstractItemView QAbstractButton {
    padding:0;
    margin:1px
    }

QListView {
    padding:1px
    }

QListView,QTreeView {
    background:<t><c k="background:base" state="list"/></t>
    }

QListView::item:!selected:hover,QTreeView::item:!selected:hover,QTreeView::branch:!selected:hover {
    background:<t><c k="list.hoverBackground"/></t>
    }

QTreeView::branch:!selected:hover,QTreeView::branch:alternate,QTreeView::branch:selected,QTreeView::branch:selected:!active {
    background:transparent
    }

QTreeView::branch {
    border-image:<t><img><c k="tree.inactiveIndentGuidesStroke"/><url id="vertical_line"/></img></t> 0
    }

QTreeView::branch:active {
    border-image:<t><img><c k="tree.indentGuidesStroke"/><url id="vertical_line"/></img></t> 0
    }

QTreeView::branch:has-siblings:adjoins-item,QTreeView::branch:!has-children:!has-siblings:adjoins-item {
    border-image:unset
    }

QTreeView::branch:has-children:!has-siblings:closed,QTreeView::branch:closed:has-children:has-siblings {
    border-image:unset;
    image:<t><img><c k="foreground:base" state="icon"/><url id="chevron_right"/></img></t>
    }

QTreeView::branch:has-children:!has-siblings:closed:disabled,QTreeView::branch:closed:has-children:has-siblings:disabled {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="chevron_right"/></img></t>
    }

QTreeView::branch:open:has-children:!has-siblings,QTreeView::branch:open:has-children:has-siblings {
    border-image:unset;
    image:<t><img><c k="foreground:base" state="icon"/><url id="expand_less" rotate="180"/></img></t>
    }

QTreeView::branch:open:has-children:!has-siblings:disabled,QTreeView::branch:open:has-children:has-siblings:disabled {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="expand_less" rotate="180"/></img></t>
    }

QTreeView > QHeaderView {
    background:<t><c k="background:base" state="list"/></t>
    }

QTreeView > QHeaderView::section {
    background:<t><c k="treeSectionHeader.background"/></t>
    }

QListView::left-arrow {
    margin:-2px;
    image:<t><img><c k="foreground:base" state="icon.unfocused"/><url id="chevron_right" rotate="180"/></img></t>
    }

QListView::right-arrow {
    margin:-2px;
    image:<t><img><c k="foreground:base" state="icon.unfocused"/><url id="chevron_right" rotate="180"/></img></t>
    }

QListView::left-arrow:selected:enabled {
    image:<t><img><c k="foreground:base" state="icon"/><url id="chevron_right" rotate="180"/></img></t>
    }

QListView::right-arrow:selected:enabled {
    image:<t><img><c k="foreground:base" state="icon"/><url id="chevron_right"/></img></t>
    }

QListView::left-arrow:disabled {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="chevron_right" rotate="180"/></img></t>
    }

QListView::right-arrow:disabled {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="chevron_right"/></img></t>
    }

QColumnView {
    background:<t><c k="background:base" state="list"/></t>
    }

QColumnViewGrip {
    margin:-4px;
    background:<t><c k="background:base" state="list"/></t>;
    image:<t><img><c k="foreground:base" state="icon"/><url id="drag_handle" rotate="90"/></img></t>
    }

QColumnViewGrip:disabled {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="drag_handle" rotate="90"/></img></t>
    }

QTableView {
    gridline-color:<t><c k="tableSectionHeader.background"/></t>;
    background:<t><c k="background:base" state="table"/></t>;
    selection-background-color:<t><c k="primary:base" state="table.selectionBackground"/></t>;
    alternate-background-color:<t><c k="table.alternateBackground"/></t>
    }

QTableView QTableCornerButton::section {
    margin:0 1px 1px 0;
    background:<t><c k="tableSectionHeader.background"/></t>;
    border-top-left-radius:2px
    }

QTableView QTableCornerButton::section:pressed {
    background:<t><c k="primary:base" state="table.selectionBackground"/></t>
    }

QTableView > QHeaderView {
    background:<t><c k="background:base" state="table"/></t>;
    border-radius:round 3px
    }

QTableView > QHeaderView::section {
    background:<t><c k="tableSectionHeader.background"/></t>
    }

QHeaderView {
    margin:0;
    border:none
    }

QHeaderView::section {
    border:none;
    background:<t><c k="treeSectionHeader.background"/></t>;
    padding-left:4px
    }

QHeaderView::section:horizontal {
    margin-right:1px
    }

QHeaderView::section:vertical {
    margin-bottom:1px
    }

QHeaderView::section:on:enabled,QHeaderView::section:on:pressed {
    color:<t><c k="primary:base"/></t>
    }

QHeaderView::section:last,QHeaderView::section:only-one {
    margin:0
    }

QHeaderView::down-arrow:horizontal {
    margin-left:-19px;
    subcontrol-position:center right;
    image:<t><img><c k="foreground:base" state="icon"/><url id="expand_less" rotate="180"/></img></t>
    }

QHeaderView::down-arrow:horizontal:disabled {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="expand_less" rotate="180"/></img></t>
    }

QHeaderView::up-arrow:horizontal {
    margin-left:-19px;
    subcontrol-position:center right;
    image:<t><img><c k="foreground:base" state="icon"/><url id="expand_less"/></img></t>
    }

QHeaderView::up-arrow:horizontal:disabled {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="expand_less"/></img></t>
    }

QHeaderView::down-arrow:vertical,QHeaderView::up-arrow:vertical {
    width:0;
    height:0
    }

QCalendarWidget > .QWidget {
    background:<t><c k="background:base" state="table"/></t>;
    border-bottom:1px solid <t><c k="border:base"/></t>;
    border-top-left-radius:round 4px;
    border-top-right-radius:round 4px
    }

QCalendarWidget > .QWidget > QWidget {
    padding:1px
    }

QCalendarWidget .QWidget > QToolButton {
    border-radius:4px
    }

QCalendarWidget > QTableView {
    margin:0;
    border:none;
    border-radius:4px;
    border-top-left-radius:0;
    border-top-right-radius:0;
    alternate-background-color:<t><c k="table.alternateBackground"/></t>;
    }

QLineEdit,QAbstractSpinBox {
    padding:3px 4px;
    min-height:1em;
    border:1px solid <t><c k="border:base" state="input"/></t>;
    background:<t><c k="input.background"/></t>;
    border-radius:4px
    }

QLineEdit:focus,QAbstractSpinBox:focus {
    border-color:<t><c k="primary:base"/></t>
    }

QAbstractSpinBox::up-button,QAbstractSpinBox::down-button {
    subcontrol-position:center right;
    border-radius:round 4px
    }

QAbstractSpinBox::up-button:hover:on,QAbstractSpinBox::down-button:hover:on {
    background:<t><c k="inputButton.hoverBackground"/></t>
    }

QAbstractSpinBox::up-button {
    bottom:5px;
    right:4px
    }

QAbstractSpinBox::up-arrow:on {
    image:<t><img><c k="foreground:base" state="icon"/><url id="arrow_drop_up"/></img></t>
    }

QAbstractSpinBox::up-arrow:disabled,QAbstractSpinBox::up-arrow:off {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="arrow_drop_up"/></img></t>
    }

QAbstractSpinBox::down-button {
    top:5px;
    right:4px
    }

QAbstractSpinBox::down-arrow:on {
    image:<t><img><c k="foreground:base" state="icon"/><url id="arrow_drop_up" rotate="180"/></img></t>
    }

QAbstractSpinBox::down-arrow:disabled,QAbstractSpinBox::down-arrow:off {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="arrow_drop_up" rotate="180"/></img></t>
    }

QDateTimeEdit::drop-down {
    padding-right:4px;
    width:16px;
    image:<t><img><c k="foreground:base" state="icon"/><url id="calendar_today"/></img></t>
    }

QDateTimeEdit::drop-down:disabled {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="calendar_today"/></img></t>
    }

QDateTimeEdit::down-arrow[calendarPopup=true] {
    image:none
    }

QFileDialog QFrame {
    border:none
    }

QFontDialog QListView {
    min-height:60px
    }

QComboBox::indicator,QMenu::indicator {
    width:18px;
    height:18px
    }

QMenu::indicator {
    background:<t><c k="popupItem.checkbox.background"/></t>;
    margin-left:3px;
    border-radius:round 4px
    }

QComboBox::indicator:checked,QMenu::indicator:checked {
    image:<t><img><c k="foreground:base" state="icon"/><url id="check"/></img></t>
    }

QCheckBox,QRadioButton {
    spacing:8px
    }

QGroupBox::title,QAbstractItemView::item {
    spacing:6px
    }

QCheckBox::indicator,QGroupBox::indicator,QAbstractItemView::indicator,QRadioButton::indicator {
    height:18px;
    width:18px
    }

QCheckBox::indicator,QGroupBox::indicator,QAbstractItemView::indicator {
    image:<t><img><c k="foreground:base" state="icon"/><url id="check_box_outline_blank"/></img></t>
    }

QCheckBox::indicator:unchecked:disabled,QGroupBox::indicator:unchecked:disabled,QAbstractItemView::indicator:unchecked:disabled {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="check_box_outline_blank"/></img></t>
    }

QCheckBox::indicator:checked,QGroupBox::indicator:checked,QAbstractItemView::indicator:checked {
    image:<t><img><c k="primary:base"/><url id="check_box"/></img></t>
    }

QCheckBox::indicator:checked:disabled,QGroupBox::indicator:checked:disabled,QAbstractItemView::indicator:checked:disabled {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="check_box"/></img></t>
    }

QCheckBox::indicator:indeterminate,QAbstractItemView::indicator:indeterminate {
    image:<t><img><c k="primary:base"/><url id="indeterminate_check_box"/></img></t>
    }

QCheckBox::indicator:indeterminate:disabled,QAbstractItemView::indicator:indeterminate:disabled {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="indeterminate_check_box"/></img></t>
    }

QRadioButton::indicator:unchecked {
    image:<t><img><c k="foreground:base" state="icon"/><url id="radio_button_unchecked"/></img></t>
    }

QRadioButton::indicator:unchecked:disabled {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="radio_button_unchecked"/></img></t>
    }

QRadioButton::indicator:checked {
    image:<t><img><c k="primary:base"/><url id="radio_button_checked"/></img></t>
    }

QRadioButton::indicator:checked:disabled {
    image:<t><img><c k="foreground:base" state="disabled"/><url id="radio_button_checked"/></img></t>
    }
    
PlotWidget {
    padding:0
    }
    
ParameterTree > .QWidget > .QWidget > .QWidget > QComboBox{
    min-height:1.2em
    }
    
ParameterTree::item,ParameterTree > .QWidget {
    background:<t><c k="background:base" state="list"/></t>;
    }
    """  # noqa: E501

TEMPLATE_STANDARD_ICONS_STYLESHEET = """

QCalendarWidget{
    leftarrow-icon:<t><img><c k="foreground:base" state="icon"/><url id="arrow_upward" rotate="270"/></img></t>;
    rightarrow-icon:<t><img><c k="foreground:base" state="icon"/><url id="arrow_upward" rotate="90"/></img></t>
    }

QCommandLinkButton{
    qproperty-icon:<t><img><c k="foreground:base" state="icon"/><url id="east"/></img></t>
    }

QDockWidget,QMdiSubWindow{
    titlebar-close-icon:<t><img><c k="foreground:base" state="icon"/><url id="close"/></img></t>;
    titlebar-normal-icon:<t><img><c k="foreground:base" state="icon"/><url id="flip_to_front"/></img></t>
    }

QFileDialog{
    backward-icon:<t><img><c k="foreground:base" state="icon"/><url id="arrow_upward" rotate="270"/></img></t>;
    filedialog-detailedview-icon:<t><img><c k="foreground:base" state="icon"/><url id="list"/></img></t>;
    filedialog-listview-icon:<t><img><c k="foreground:base" state="icon"/><url id="grid_view"/></img></t>;
    filedialog-new-directory-icon:<t><img><c k="foreground:base" state="icon"/><url id="create_new_folder"/></img></t>;
    filedialog-parent-directory-icon:<t><img><c k="foreground:base" state="icon"/><url id="arrow_upward"/></img></t>;
    forward-icon:<t><img><c k="foreground:base" state="icon"/><url id="arrow_upward" rotate="90"/></img></t>
    }

QLineEdit{
    lineedit-clear-button-icon:<t><img><c k="foreground:base" state="icon"/><url id="close"/></img></t>
    }

QMdiSubWindow{
    titlebar-maximize-icon:<t><img><c k="foreground:base" state="icon"/><url id="fullscreen"/></img></t>;
    titlebar-minimize-icon:<t><img><c k="foreground:base" state="icon"/><url id="minimize"/></img></t>
    }

QToolBarExtension{
    qproperty-icon:<t><img><c k="foreground:base" state="icon"/><url id="double_arrow"/></img></t>
    }
    """
