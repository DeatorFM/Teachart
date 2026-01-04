// Generated from SVG file ic_bold.svg
import QtQuick
import QtQuick.VectorImage
import QtQuick.VectorImage.Helpers
import QtQuick.Shapes

Item {
    implicitWidth: 24
    implicitHeight: 24
    component AnimationsInfo : QtObject
    {
        property bool paused: false
        property int loops: 1
        signal restart()
    }
    property AnimationsInfo animations : AnimationsInfo {}
    transform: [
        Scale { xScale: width / 24; yScale: height / 24 }
    ]
    id: __qt_toplevel
    Shape {
        id: _qt_node0
        ShapePath {
            id: _qt_shapePath_0
            strokeColor: "transparent"
            fillColor: "#ff000000"
            fillRule: ShapePath.WindingFill
            PathSvg { path: "M 8 11 L 12.5 11 C 13.8807 11 15 9.88071 15 8.5 C 15 7.11929 13.8807 6 12.5 6 L 8 6 L 8 11 M 18 15.5 C 18 17.9853 15.9853 20 13.5 20 L 6 20 L 6 4 L 12.5 4 C 14.3007 4.00008 15.928 5.07364 16.6367 6.72907 C 17.3454 8.3845 16.9989 10.303 15.756 11.606 C 17.1453 12.4105 18.0005 13.8945 18 15.5 M 8 13 L 8 18 L 13.5 18 C 14.8807 18 16 16.8807 16 15.5 C 16 14.1193 14.8807 13 13.5 13 L 8 13 " }
        }
    }
}
