from typing import List, Optional

import omni
import omni.ui as ui

from .style import ATTR_LABEL_WIDTH, BLOCK_HEIGHT, cl, fl
from .custom_base_widget import CustomBaseWidget

SPACING = 5  

class CustomComboboxWidget(CustomBaseWidget):
    """A customized combobox widget"""

    def __init__(self,
                 model: ui.AbstractItemModel = None,
                 options: List[str] = None,
                 default_value=0,
                 **kwargs):
        self.__default_val = default_value
        self.__options = options or ["1", "2", "3"]
        self.__combobox_widget = None

        # Call at the end, rather than start, so build_fn runs after all the init stuff
        CustomBaseWidget.__init__(self, model=model, **kwargs)

    def destroy(self):
        CustomBaseWidget.destroy()
        self.__options = None
        self.__combobox_widget = None

    @property
    def model(self) -> Optional[ui.AbstractItemModel]:
        """The widget's model"""
        if self.__combobox_widget:
            return self.__combobox_widget.model

    @model.setter
    def model(self, value: ui.AbstractItemModel):
        """The widget's model"""
        self.__combobox_widget.model = value

    def _on_value_changed(self, *args):
        """Set revert_img to correct state."""
        model = self.__combobox_widget.model
        index = model.get_item_value_model().get_value_as_int()
        self.revert_img.enabled = self.__default_val != index

    def _restore_default(self):
        """Restore the default value."""
        if self.revert_img.enabled:
            self.__combobox_widget.model.get_item_value_model().set_value(
                self.__default_val)
            self.revert_img.enabled = False

    def _build_body(self):
        """Main meat of the widget.  Draw the Rectangle, Combobox, and
        set up callbacks to keep them updated.
        """
        with ui.HStack():
            with ui.ZStack():
                # TODO: Simplify when borders on ComboBoxes work in Kit!
                # and remove style rule for "combobox" Rect

                # Use the outline from the Rectangle for the Combobox
                ui.Rectangle(name="combobox",
                             height=BLOCK_HEIGHT)

                option_list = list(self.__options)
                self.__combobox_widget = ui.ComboBox(
                    0, *option_list,
                    name="dropdown_menu",
                    # Abnormal height because this "transparent" combobox
                    # has to fit inside the Rectangle behind it
                    height=10
                )

                # Swap for  different dropdown arrow image over current one
                with ui.HStack():
                    ui.Spacer()  # Keep it on the right side
                    with ui.VStack(width=0):  # Need width=0 to keep right-aligned
                        ui.Spacer(height=5)
                        with ui.ZStack():
                            ui.Rectangle(width=15, height=15, name="combobox_icon_cover")
                            ui.Image(name="collapsable_closed", width=12, height=12)
                    ui.Spacer(width=2)  # Right margin

            ui.Spacer(width=ui.Percent(30))

        self.__combobox_widget.model.add_item_changed_fn(self._on_value_changed)


class CustomBoolWidget(CustomBaseWidget):
    """A custom checkbox or switch widget"""

    def __init__(self,
                 model: ui.AbstractItemModel = None,
                 default_value: bool = True,
                 on_checked_fn: callable = None,
                 **kwargs):
        self.__default_val = default_value
        self.__bool_image = None
        self.on_checked_fn = on_checked_fn

        # Call at the end, rather than start, so build_fn runs after all the init stuff
        CustomBaseWidget.__init__(self, model=model, **kwargs)

    def destroy(self):
        CustomBaseWidget.destroy()
        self.__bool_image = None

    def _restore_default(self):
        """Restore the default value."""
        if self.revert_img.enabled:
            # self.__bool_image.checked = self.__default_val
            # self.__bool_image.name = (
            #     "checked" if self.__bool_image.checked else "unchecked"
            # )
            # self.revert_img.enabled = False
            self._on_value_changed()

    def _on_value_changed(self):
        """Swap checkbox images and set revert_img to correct state."""
        self.__bool_image.checked = not self.__bool_image.checked
        self.__bool_image.name = (
            "checked" if self.__bool_image.checked else "unchecked"
        )
        self.revert_img.enabled = self.__default_val != self.__bool_image.checked
        
        if self.on_checked_fn:
            self.on_checked_fn(self.__bool_image.checked)

    def _build_body(self):
        """Main meat of the widget.  Draw the appropriate checkbox image, and
        set up callback.
        """
        with ui.HStack():
            with ui.VStack():
                # Just shift the image down slightly (2 px) so it's aligned the way
                # all the other rows are.
                ui.Spacer(height=2)
                self.__bool_image = ui.Image(
                    name="checked" if self.__default_val else "unchecked",
                    fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT,
                    height=16, width=16, checked=self.__default_val
                )
            # Let this spacer take up the rest of the Body space.
            ui.Spacer()

        self.__bool_image.set_mouse_pressed_fn(
            lambda x, y, b, m: self._on_value_changed())


NUM_FIELD_WIDTH = 50
SLIDER_WIDTH = ui.Percent(100)
FIELD_HEIGHT = 22  # TODO: Once Field padding is fixed, this should be 18
SPACING = 4
TEXTURE_NAME = "slider_bg_texture"


class CustomSliderWidget(CustomBaseWidget):
    """A compound widget for scalar slider input, which contains a
    Slider and a Field with text input next to it.
    """

    def __init__(self,
                 model: ui.AbstractItemModel = None,
                 num_type: str = "int",
                 min=0.0,
                 max=1.0,
                 default_val=0.0,
                 display_range: bool = False,
                 on_slide_fn: callable = None,
                 **kwargs):
        self.__slider: Optional[ui.AbstractSlider] = None
        self.__numberfield: Optional[ui.AbstractField] = None
        self.__min = min
        self.__max = max
        self.__default_val = default_val
        self.__num_type = num_type
        self.__display_range = display_range
        self.on_slide_fn = on_slide_fn

        # Call at the end, rather than start, so build_fn runs after all the init stuff
        CustomBaseWidget.__init__(self, model=model, **kwargs)

    def destroy(self):
        CustomBaseWidget.destroy()
        self.__slider = None
        self.__numberfield = None

    @property
    def model(self) -> Optional[ui.AbstractItemModel]:
        """The widget's model"""
        if self.__slider:
            return self.__slider.model

    @model.setter
    def model(self, value: ui.AbstractItemModel):
        """The widget's model"""
        self.__slider.model = value
        self.__numberfield.model = value

    def _on_value_changed(self, *args):
        """Set revert_img to correct state."""
        if self.__num_type == "float":
            index = self.model.as_float
        else:
            index = self.model.as_int
        self.revert_img.enabled = self.__default_val != index

        if self.on_slide_fn:
            self.on_slide_fn(index)

    def _restore_default(self):
        """Restore the default value."""
        if self.revert_img.enabled:
            self.model.set_value(self.__default_val)
            self.revert_img.enabled = False

    def _build_display_range(self):
        """Builds just the tiny text range under the slider."""
        with ui.HStack():
            ui.Label(str(self.__min), alignment=ui.Alignment.LEFT, name="range_text")
            if self.__min < 0 and self.__max > 0:
                # Add middle value (always 0), but it may or may not be centered,
                # depending on the min/max values.
                total_range = self.__max - self.__min
                # subtract 25% to account for end number widths
                left = 100 * abs(0 - self.__min) / total_range - 25
                right = 100 * abs(self.__max - 0) / total_range - 25
                ui.Spacer(width=ui.Percent(left))
                ui.Label("0", alignment=ui.Alignment.CENTER, name="range_text")
                ui.Spacer(width=ui.Percent(right))
            else:
                ui.Spacer()
            ui.Label(str(self.__max), alignment=ui.Alignment.RIGHT, name="range_text")
        ui.Spacer(height=.75)

    def _build_body(self):
        """Main meat of the widget.  Draw the Slider, display range text, Field,
        and set up callbacks to keep them updated.
        """
        with ui.HStack(spacing=0):
            # the user provided a list of default values
            with ui.VStack(spacing=3, width=ui.Fraction(3)):
                with ui.ZStack():
                    # Put texture image here, with rounded corners, then make slider
                    # bg be fully transparent, and fg be gray and partially transparent
                    with ui.Frame(width=SLIDER_WIDTH, height=FIELD_HEIGHT,
                                  horizontal_clipping=True):
                        # Spacing is negative because "tileable" texture wasn't
                        # perfectly tileable, so that adds some overlap to line up better.
                        with ui.HStack(spacing=-12):
                            for i in range(50):  # tiling the texture
                                ui.Image(name=TEXTURE_NAME,
                                         fill_policy=ui.FillPolicy.PRESERVE_ASPECT_CROP,
                                         width=50,)

                    slider_cls = (
                        ui.FloatSlider if self.__num_type == "float" else ui.IntSlider
                    )
                    self.__slider = slider_cls(
                        height=FIELD_HEIGHT,
                        min=self.__min, max=self.__max, name="attr_slider"
                    )

                if self.__display_range:
                    self._build_display_range()

            with ui.VStack(width=ui.Fraction(1)):
                model = self.__slider.model
                model.set_value(self.__default_val)
                field_cls = (
                    ui.FloatField if self.__num_type == "float" else ui.IntField
                )

                # Note: This is a hack to allow for text to fill the Field space more, as there was a bug
                # with Field padding.  It is fixed, and will be available in the next release of Kit.
                with ui.ZStack():
                    # height=FIELD_HEIGHT-1 to account for the border, so the field isn't
                    # slightly taller than the slider
                    ui.Rectangle(
                        style_type_name_override="Field",
                        name="attr_field",
                        height=FIELD_HEIGHT - 1
                    )
                    with ui.HStack(height=0):
                        ui.Spacer(width=2)
                        self.__numberfield = field_cls(
                            model,
                            height=0,
                            style={
                                "background_color": cl.transparent,
                                "border_color": cl.transparent,
                                "padding": 4,
                                "font_size": fl.field_text_font_size,
                            },
                        )
                if self.__display_range:
                    ui.Spacer()

        model.add_value_changed_fn(self._on_value_changed)


class CustomSkySelectionGroup(CustomBaseWidget):
    def __init__(self,
        on_select_fn: callable = None 
    ) -> None:
        self.on_select_fn = on_select_fn
        self.sky_type = ""
        CustomBaseWidget.__init__(self, label = "Sky type:")

    def _build_body(self):
        with ui.HStack():
            self.button_clear = ui.Button("Sunny", name = "control_button")
            self.button_cloudy = ui.Button("Cloudy", name = "control_button")
            self.button_overcast = ui.Button("Overcast", name = "control_button")
            self.button_night = ui.Button("Night", name = "control_button")

        self.button_clear.set_clicked_fn(lambda : self._on_button("clear"))
        self.button_cloudy.set_clicked_fn(lambda : self._on_button("cloudy"))
        self.button_overcast.set_clicked_fn(lambda : self._on_button("overcast"))
        self.button_night.set_clicked_fn(lambda : self._on_button("night"))

        self.button_list = [self.button_clear, self.button_cloudy, self.button_overcast,  self.button_night]

    def enable_buttons(self):
        for button in self.button_list:
            button.enabled = True
            button.name = "control_button"

    def _on_button(self, sky_type:str):
        if self.on_select_fn:
            self.on_select_fn(sky_type.capitalize())
        self.enable_buttons()
        button = getattr(self, f"button_{sky_type}")
        button.name = f"control_button_pressed{2}"
        self.revert_img.enabled = True

    def _restore_default(self):
        """Restore the default value."""
        if self.revert_img.enabled:
            self.revert_img.enabled = False
            self.enable_buttons()
            self.on_select_fn("")

class CustomFlowSelectionGroup(CustomBaseWidget):
    def __init__(self,
        on_select_fn: callable = None 
    ) -> None:
        self.on_select_fn = on_select_fn
        self.sky_type = ""
        CustomBaseWidget.__init__(self, label = "Flow type:")

    def _build_body(self):
        with ui.HStack():
            self.button_fire = ui.Button("Fire", name = "control_button")
            self.button_smoke = ui.Button("Smoke", name = "control_button")
            self.button_dust = ui.Button("Dust", name = "control_button")

        self.button_fire.set_clicked_fn(lambda : self._on_button("fire"))
        self.button_smoke.set_clicked_fn(lambda : self._on_button("smoke"))
        self.button_dust.set_clicked_fn(lambda : self._on_button("dust"))

        self.button_list = [self.button_fire, self.button_smoke, self.button_dust]

    def enable_buttons(self):
        for button in self.button_list:
            button.enabled = True
            button.name = "control_button"

    def _on_button(self, flow_type:str):
        if self.on_select_fn:
            self.on_select_fn(flow_type.capitalize())

        self.enable_buttons()
        button = getattr(self, f"button_{flow_type}")
        button.name = f"control_button_pressed{2}"
        self.revert_img.enabled = True

    def _restore_default(self):
        """Restore the default value."""
        if self.revert_img.enabled:
            self.revert_img.enabled = False
            self.enable_buttons()
            self.on_select_fn("")


class CustomStringField(CustomBaseWidget):
    def __init__(self,
        label:str,
        string_ui_name = "input_text"
    ) -> None:
        self.label = label
        self.string_ui_name = string_ui_name
        CustomBaseWidget.__init__(self, label = label)

    def _build_body(self):
        with ui.HStack():
            string_ui = ui.StringField(height = 20, width = 100)

        self.model = string_ui.model
        self.model.set_value("Q")

    def _build_tail(self):
        return 

import subprocess, os, platform

class CustomPathButtonWidget:
    """A compound widget for holding a path in a StringField, and a button
    that can perform an action.
    TODO: Get text ellision working in the path field, to start with "..."
    """
    def __init__(self,
                 label: str,
                 path: str,
                 btn_callback: callable = None):
        self.__attr_label = label
        self.__pathfield: ui.StringField = None
        self.__path = path
        self.__btn = None
        self.__callback = btn_callback
        self.__frame = ui.Frame()

        with self.__frame:
            self._build_fn()

    def destroy(self):
        self.__pathfield = None
        self.__btn = None
        self.__callback = None
        self.__frame = None

    @property
    def model(self) -> Optional[ui.AbstractItem]:
        """The widget's model"""
        if self.__pathfield:
            return self.__pathfield.model

    @model.setter
    def model(self, value: ui.AbstractItem):
        """The widget's model"""
        self.__pathfield.model = value

    def get_path(self):
        return self.model.as_string

    def _build_fn(self):
        """Draw all of the widget parts and set up callbacks."""
        with ui.HStack():
            ui.Label(
                self.__attr_label,
                name="attribute_name",
                width=120,
            )
            self.__pathfield = ui.StringField(
                name="path_field",
                enabled = False,
            )

            ui.Spacer(width = 8)
            
            # # TODO: Add clippingType=ELLIPSIS_LEFT for long paths
            self.__pathfield.model.set_value(self.__path)

            self.folder_img = ui.Image(
                name="open_folder",
                fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT,
                width=12,
                height=18,
            )

            self.folder_img.set_mouse_pressed_fn(lambda x, y, b, m: self.open_path(self.__path))

    def open_path(self, path):
        if platform.system() == "Darwin":  # macOS
            subprocess.call(("open", path))
        elif platform.system() == "Windows":  # Windows
            os.startfile(path)
        else:  # linux variants
            subprocess.call(("xdg-open", path))
