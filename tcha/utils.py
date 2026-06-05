import ctypes
from ctypes import wintypes

from tcha.consts import DisplayMode


def evened(dec: float) -> int | float:
    """Returns a float as an even integer if possible else input and output are the same"""
    return dec if dec % 1 > 0 else int(dec)


class WinApi:
    SDC_TOPOLOGY_INTERNAL = 0x00000001
    SDC_TOPOLOGY_CLONE = 0x00000002  # Duplicate mode
    SDC_TOPOLOGY_EXTEND = 0x00000004  # Extended mode
    SDC_TOPOLOGY_EXTERNAL = 0x00000008
    SDC_APPLY = 0x00000080
    QDC_ONLY_ACTIVE_PATHS = 0x00000002

    @staticmethod
    def display_count() -> int:
        user32 = ctypes.windll.LoadLibrary("user32")

        num_paths = wintypes.UINT(0)
        num_modes = wintypes.UINT(0)

        # Query buffer sizes
        user32.GetDisplayConfigBufferSizes(
            WinApi.QDC_ONLY_ACTIVE_PATHS,
            ctypes.byref(num_paths),
            ctypes.byref(num_modes),
        )

        return num_paths.value

    @staticmethod
    def get_display_mode() -> DisplayMode:
        user32 = ctypes.windll.LoadLibrary("user32")

        num_paths = wintypes.UINT(0)
        num_modes = wintypes.UINT(0)

        # Query buffer sizes
        result = user32.GetDisplayConfigBufferSizes(
            WinApi.QDC_ONLY_ACTIVE_PATHS,
            ctypes.byref(num_paths),
            ctypes.byref(num_modes),
        )

        if result != 0:
            return DisplayMode.Single

        # num_paths.value tells you how many active display paths exist
        display_count = num_paths.value

        print(f"Active display paths: {display_count}")
        virtual_width = user32.GetSystemMetrics(78)
        primary_width = user32.GetSystemMetrics(0)

        if display_count > 1:
            if virtual_width > primary_width:
                return DisplayMode.Extended
            else:
                return DisplayMode.Duplicated
        return DisplayMode.Single

    @staticmethod
    def set_display_mode(mode: DisplayMode) -> None:
        user32 = ctypes.windll.LoadLibrary("user32")
        if mode == DisplayMode.Single:
            print("Single mode cannot be forced.")
            return
        elif mode == DisplayMode.Extended:
            user32.SetDisplayConfig(
                0, None, 0, None, WinApi.SDC_APPLY | WinApi.SDC_TOPOLOGY_EXTEND
            )
        else:
            user32.SetDisplayConfig(
                0, None, 0, None, WinApi.SDC_APPLY | WinApi.SDC_TOPOLOGY_CLONE
            )
