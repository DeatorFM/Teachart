import QtQuick 2.0
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.1
import QtQuick.Window 2.1
import io.qt.textproperties 1.0

ApplicationWindow {
    id: MainView
    width: 800
    height: 400
    title: "Teachart"

    ColumnLayout {
        id: central_layout
        spacing: 0

        TabBar {
            id: tabs
            width: parent.width

            TabButton {
                text: qsTr("Start")
            }

        StackLayout {
            id: tabview
            width: parent.width
            currentIndex: tabs.currentIndex
        }
        }
    }
}