# ------------------------------------------------------------
# ui/keyboard.py
# Tractor Board - Touch Bildschirmtastatur
# ------------------------------------------------------------

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


# ------------------------------------------------------------
# Farben
# ------------------------------------------------------------

KEY_COLOR = (
    0.18,
    0.20,
    0.20,
    1
)

SPECIAL_COLOR = (
    0.12,
    0.35,
    0.55,
    1
)

ENTER_COLOR = (
    0.15,
    0.60,
    0.25,
    1
)

DELETE_COLOR = (
    0.65,
    0.15,
    0.15,
    1
)


# ------------------------------------------------------------
# Bildschirmtastatur
# ------------------------------------------------------------

class TouchKeyboard(BoxLayout):

    def __init__(
        self,
        target,
        numeric=False,
        on_done=None,
        **kwargs
    ):

        super().__init__(
            orientation="vertical",
            spacing=dp(5),
            padding=dp(5),
            size_hint_y=None,
            height=dp(250),
            **kwargs
        )

        self.target = target
        self.numeric = numeric
        self.on_done_callback = on_done

        self.shift = False

        self.build_keyboard()


    # ========================================================
    # TASTATUR AUFBAUEN
    # ========================================================

    def build_keyboard(self):

        self.clear_widgets()

        if self.numeric:

            self.build_numeric_keyboard()

        else:

            self.build_text_keyboard()


    # ========================================================
    # TEXTTASTATUR
    # ========================================================

    def build_text_keyboard(self):

        rows = [
            [
                "Q", "W", "E", "R", "T",
                "Z", "U", "I", "O", "P",
                "Ü"
            ],
            [
                "A", "S", "D", "F", "G",
                "H", "J", "K", "L",
                "Ö", "Ä"
            ],
            [
                "Y", "X", "C", "V", "B",
                "N", "M", ",", ".", "-"
            ]
        ]


        for row in rows:

            row_layout = BoxLayout(
                orientation="horizontal",
                spacing=dp(4)
            )

            for key in row:

                button = self.create_key(
                    key
                )

                row_layout.add_widget(
                    button
                )

            self.add_widget(
                row_layout
            )


        # ----------------------------------------------------
        # Untere Reihe
        # ----------------------------------------------------

        bottom = BoxLayout(
            orientation="horizontal",
            spacing=dp(4)
        )


        shift_button = Button(
            text="⇧",
            font_size="22sp",
            background_color=SPECIAL_COLOR
        )

        shift_button.bind(
            on_release=self.toggle_shift
        )

        bottom.add_widget(
            shift_button
        )


        space_button = Button(
            text="LEER",
            font_size="20sp",
            background_color=KEY_COLOR
        )

        space_button.bind(
            on_release=self.insert_space
        )

        bottom.add_widget(
            space_button
        )


        delete_button = Button(
            text="⌫",
            font_size="25sp",
            background_color=DELETE_COLOR
        )

        delete_button.bind(
            on_release=self.delete_character
        )

        bottom.add_widget(
            delete_button
        )


        done_button = Button(
            text="FERTIG",
            font_size="20sp",
            background_color=ENTER_COLOR
        )

        done_button.bind(
            on_release=self.done
        )

        bottom.add_widget(
            done_button
        )


        self.add_widget(
            bottom
        )


    # ========================================================
    # NUMERISCHE TASTATUR
    # ========================================================

    def build_numeric_keyboard(self):

        rows = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            [".", "0", ","]
        ]


        for row in rows:

            row_layout = BoxLayout(
                orientation="horizontal",
                spacing=dp(4)
            )

            for key in row:

                button = self.create_key(
                    key
                )

                row_layout.add_widget(
                    button
                )

            self.add_widget(
                row_layout
            )


        bottom = BoxLayout(
            orientation="horizontal",
            spacing=dp(4)
        )


        delete_button = Button(
            text="⌫",
            font_size="25sp",
            background_color=DELETE_COLOR
        )

        delete_button.bind(
            on_release=self.delete_character
        )

        bottom.add_widget(
            delete_button
        )


        minus_button = Button(
            text="-",
            font_size="25sp",
            background_color=KEY_COLOR
        )

        minus_button.bind(
            on_release=lambda instance:
            self.insert_text("-")
        )

        bottom.add_widget(
            minus_button
        )


        done_button = Button(
            text="FERTIG",
            font_size="20sp",
            background_color=ENTER_COLOR
        )

        done_button.bind(
            on_release=self.done
        )

        bottom.add_widget(
            done_button
        )


        self.add_widget(
            bottom
        )


    # ========================================================
    # TASTE ERZEUGEN
    # ========================================================

    def create_key(
        self,
        key
    ):

        button = Button(
            text=key,
            font_size="22sp",
            background_color=KEY_COLOR
        )

        button.bind(
            on_release=lambda instance,
            value=key:
            self.insert_text(value)
        )

        return button


    # ========================================================
    # TEXT EINFÜGEN
    # ========================================================

    def insert_text(
        self,
        text
    ):

        if self.target is None:

            return


        if self.shift:

            text = text.upper()

        else:

            text = text.lower()


        self.target.insert_text(
            text
        )


    # ========================================================
    # LEERZEICHEN
    # ========================================================

    def insert_space(
        self,
        instance
    ):

        if self.target is None:

            return


        self.target.insert_text(
            " "
        )


    # ========================================================
    # LÖSCHEN
    # ========================================================

    def delete_character(
        self,
        instance
    ):

        if self.target is None:

            return


        text = self.target.text

        cursor = self.target.cursor_index()


        if cursor <= 0:

            return


        self.target.text = (
            text[:cursor - 1]
            +
            text[cursor:]
        )


        self.target.cursor = (
            max(0, cursor - 1)
        )


    # ========================================================
    # SHIFT
    # ========================================================

    def toggle_shift(
        self,
        instance
    ):

        self.shift = not self.shift


    # ========================================================
    # FERTIG
    # ========================================================

    def done(
        self,
        instance
    ):

        if self.on_done_callback:

            self.on_done_callback()

