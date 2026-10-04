# ------------------------------------------------------------
# ui/machine_manager.py
# Tractor Board - Maschinenverwaltung
# ------------------------------------------------------------

from kivy.metrics import dp
from kivy.clock import Clock

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput

from ui.keyboard import TouchKeyboard


# ------------------------------------------------------------
# Farben
# ------------------------------------------------------------

BG_COLOR = (
    0.06,
    0.07,
    0.07,
    1
)

GREEN = (
    0.20,
    0.70,
    0.25,
    1
)

RED = (
    0.80,
    0.15,
    0.15,
    1
)

BLUE = (
    0.15,
    0.40,
    0.75,
    1
)

WHITE = (
    1,
    1,
    1,
    1
)


# ------------------------------------------------------------
# Label
# ------------------------------------------------------------

def make_label(
    text="",
    font_size="20sp",
    bold=False
):

    label = Label(
        text=text,
        font_size=font_size,
        bold=bold,
        color=WHITE,
        halign="left",
        valign="middle"
    )

    label.bind(
        size=lambda instance, value:
        setattr(
            instance,
            "text_size",
            value
        )
    )

    return label


# ------------------------------------------------------------
# Machine Manager
# ------------------------------------------------------------

class MachineManager(FloatLayout):

    def __init__(
        self,
        app,
        database,
        **kwargs
    ):

        super().__init__(
            **kwargs
        )

        self.app = app
        self.database = database

        self.current_type = "tractor"

        self.selected_id = None

        self.inputs = {}

        self.keyboard = None

        self.build_ui()

        self.show_tractor_list()


    # ========================================================
    # HAUPT UI
    # ========================================================

    def build_ui(self):

        self.main = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(10)
        )

        self.add_widget(
            self.main
        )


        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(65)
        )

        title = make_label(
            text="MASCHINENVERWALTUNG",
            font_size="30sp",
            bold=True
        )

        title.halign = "center"

        header.add_widget(
            title
        )

        self.main.add_widget(
            header
        )


        # ----------------------------------------------------
        # TYP
        # ----------------------------------------------------

        type_bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(60),
            spacing=dp(10)
        )


        tractor_button = Button(
            text="TRAKTOREN",
            font_size="21sp",
            background_color=BLUE
        )

        tractor_button.bind(
            on_release=self.show_tractor_list
        )

        type_bar.add_widget(
            tractor_button
        )


        implement_button = Button(
            text="ANBAUGERÄTE",
            font_size="21sp",
            background_color=BLUE
        )

        implement_button.bind(
            on_release=self.show_implement_list
        )

        type_bar.add_widget(
            implement_button
        )


        self.main.add_widget(
            type_bar
        )


        # ----------------------------------------------------
        # CONTENT
        # ----------------------------------------------------

        self.content = BoxLayout(
            orientation="vertical",
            spacing=dp(10)
        )

        self.main.add_widget(
            self.content
        )


        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        footer = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(70)
        )


        back_button = Button(
            text="ZURÜCK",
            font_size="23sp"
        )

        back_button.bind(
            on_release=self.go_back
        )

        footer.add_widget(
            back_button
        )


        self.main.add_widget(
            footer
        )


    # ========================================================
    # TASTATUR
    # ========================================================

    def show_keyboard(
        self,
        text_input
    ):

        self.hide_keyboard()


        numeric = (
            text_input.input_type == "number"
        )


        self.keyboard = TouchKeyboard(
            target=text_input,
            numeric=numeric,
            on_done=self.hide_keyboard
        )


        self.keyboard.size_hint = (
            1,
            None
        )

        self.keyboard.height = dp(270)


        # ----------------------------------------------------
        # Tastatur unten platzieren
        # ----------------------------------------------------

        self.keyboard.pos_hint = {
            "x": 0,
            "y": 0
        }


        self.add_widget(
            self.keyboard
        )


        # ----------------------------------------------------
        # Tastatur nach vorne
        # ----------------------------------------------------

        self.keyboard.canvas.ask_update()


    # ========================================================
    # TASTATUR AUSBLENDEN
    # ========================================================

    def hide_keyboard(self):

        if self.keyboard is not None:

            try:

                self.remove_widget(
                    self.keyboard
                )

            except Exception:

                pass


            self.keyboard = None


    # ========================================================
    # INPUT
    # ========================================================

    def create_input(
        self,
        key,
        value="",
        numeric=False,
        multiline=False
    ):

        input_field = TextInput(
            text=value,
            font_size="22sp",
            multiline=multiline,
            input_type=(
                "number"
                if numeric
                else "text"
            ),
            padding=[
                dp(15),
                dp(15),
                dp(15),
                dp(15)
            ],
            size_hint_y=None,
            height=dp(
                110
                if multiline
                else 65
            )
        )


        input_field.bind(
            focus=self.input_focus
        )


        self.inputs[key] = input_field


        return input_field


    # ========================================================
    # FOCUS
    # ========================================================

    def input_focus(
        self,
        instance,
        focused
    ):

        if focused:

            self.show_keyboard(
                instance
            )

        else:

            # Nicht sofort schließen,
            # da der Fokus beim Drücken
            # der Kivy-Tastatur wechseln kann.
            Clock.schedule_once(
                self.check_keyboard_focus,
                0.1
            )


    # ========================================================
    # FOCUS PRÜFEN
    # ========================================================

    def check_keyboard_focus(
        self,
        dt
    ):

        for field in self.inputs.values():

            if field.focus:

                return


        # Tastatur nur schließen,
        # wenn kein Eingabefeld mehr aktiv ist.

        # self.hide_keyboard()
        #
        # Absichtlich nicht automatisch schließen.
        # "FERTIG" übernimmt das explizit.


    # ========================================================
    # TRAKTOR LISTE
    # ========================================================

    def show_tractor_list(
        self,
        instance=None
    ):

        self.hide_keyboard()

        self.current_type = "tractor"

        self.selected_id = None

        self.clear_content()


        self.content.add_widget(
            make_label(
                text="TRAKTOREN",
                font_size="26sp",
                bold=True
            )
        )


        scroll = ScrollView(
            do_scroll_x=False
        )


        list_layout = GridLayout(
            cols=1,
            spacing=dp(8),
            padding=dp(5),
            size_hint_y=None
        )

        list_layout.bind(
            minimum_height=list_layout.setter(
                "height"
            )
        )


        tractors = self.database.get_tractors()


        for tractor in tractors:

            button = Button(
                text=self.format_tractor(
                    tractor
                ),
                font_size="20sp",
                size_hint_y=None,
                height=dp(70)
            )

            button.bind(
                on_release=lambda instance,
                machine_id=tractor["id"]:
                self.select_machine(
                    machine_id
                )
            )

            list_layout.add_widget(
                button
            )


        scroll.add_widget(
            list_layout
        )

        self.content.add_widget(
            scroll
        )


        action_bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(70),
            spacing=dp(10)
        )


        new_button = Button(
            text="NEUER TRAKTOR",
            font_size="21sp",
            background_color=GREEN
        )

        new_button.bind(
            on_release=self.new_tractor
        )

        action_bar.add_widget(
            new_button
        )


        delete_button = Button(
            text="LÖSCHEN",
            font_size="21sp",
            background_color=RED
        )

        delete_button.bind(
            on_release=self.delete_selected
        )

        action_bar.add_widget(
            delete_button
        )


        self.content.add_widget(
            action_bar
        )


    # ========================================================
    # ANBAUGERÄTE LISTE
    # ========================================================

    def show_implement_list(
        self,
        instance=None
    ):

        self.hide_keyboard()

        self.current_type = "implement"

        self.selected_id = None

        self.clear_content()


        self.content.add_widget(
            make_label(
                text="ANBAUGERÄTE",
                font_size="26sp",
                bold=True
            )
        )


        scroll = ScrollView(
            do_scroll_x=False
        )


        list_layout = GridLayout(
            cols=1,
            spacing=dp(8),
            padding=dp(5),
            size_hint_y=None
        )

        list_layout.bind(
            minimum_height=list_layout.setter(
                "height"
            )
        )


        implements = (
            self.database.get_implements()
        )


        for implement in implements:

            button = Button(
                text=self.format_implement(
                    implement
                ),
                font_size="20sp",
                size_hint_y=None,
                height=dp(70)
            )

            button.bind(
                on_release=lambda instance,
                machine_id=implement["id"]:
                self.select_machine(
                    machine_id
                )
            )

            list_layout.add_widget(
                button
            )


        scroll.add_widget(
            list_layout
        )

        self.content.add_widget(
            scroll
        )


        action_bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(70),
            spacing=dp(10)
        )


        new_button = Button(
            text="NEUES ANBAUGERÄT",
            font_size="20sp",
            background_color=GREEN
        )

        new_button.bind(
            on_release=self.new_implement
        )

        action_bar.add_widget(
            new_button
        )


        delete_button = Button(
            text="LÖSCHEN",
            font_size="21sp",
            background_color=RED
        )

        delete_button.bind(
            on_release=self.delete_selected
        )

        action_bar.add_widget(
            delete_button
        )


        self.content.add_widget(
            action_bar
        )


    # ========================================================
    # TRAKTOR FORMAT
    # ========================================================

    def format_tractor(
        self,
        tractor
    ):

        text = tractor["name"]

        if tractor["manufacturer"]:

            text += (
                " | "
                + tractor["manufacturer"]
            )

        if tractor["model"]:

            text += (
                " "
                + tractor["model"]
            )

        return text


    # ========================================================
    # ANBAUGERÄT FORMAT
    # ========================================================

    def format_implement(
        self,
        implement
    ):

        text = implement["name"]

        if implement["manufacturer"]:

            text += (
                " | "
                + implement["manufacturer"]
            )

        if implement["model"]:

            text += (
                " "
                + implement["model"]
            )

        return text


    # ========================================================
    # TRAKTOR NEU
    # ========================================================

    def new_tractor(
        self,
        instance
    ):

        self.current_type = "tractor"

        self.selected_id = None

        self.build_tractor_form()


    # ========================================================
    # ANBAUGERÄT NEU
    # ========================================================

    def new_implement(
        self,
        instance
    ):

        self.current_type = "implement"

        self.selected_id = None

        self.build_implement_form()


    # ========================================================
    # TRAKTOR FORMULAR
    # ========================================================

    def build_tractor_form(
        self,
        data=None
    ):

        self.hide_keyboard()

        self.clear_content()

        self.inputs = {}


        self.content.add_widget(
            make_label(
                text="TRAKTOR",
                font_size="27sp",
                bold=True
            )
        )


        scroll = ScrollView(
            do_scroll_x=False
        )


        form = GridLayout(
            cols=2,
            spacing=dp(12),
            padding=dp(10),
            size_hint_y=None
        )

        form.bind(
            minimum_height=form.setter(
                "height"
            )
        )


        fields = [
            ("name", "Bezeichnung", False),
            ("manufacturer", "Hersteller", False),
            ("model", "Modell", False),
            ("year", "Baujahr", True),
            ("length", "Länge [m]", True),
            ("width", "Breite [m]", True),
            ("height", "Höhe [m]", True),
            ("wheelbase", "Radstand [m]", True),
            ("front_track", "Spur vorne [m]", True),
            ("rear_track", "Spur hinten [m]", True),
            ("weight", "Gewicht [kg]", True),
            ("notes", "Notizen", False)
        ]


        for key, caption, numeric in fields:

            label = make_label(
                text=caption,
                font_size="20sp"
            )

            label.size_hint_y = None
            label.height = dp(
                110
                if key == "notes"
                else 65
            )

            form.add_widget(
                label
            )


            value = ""

            if data is not None:

                if data[key] is not None:

                    value = str(
                        data[key]
                    )


            input_field = self.create_input(
                key=key,
                value=value,
                numeric=numeric,
                multiline=(
                    key == "notes"
                )
            )


            form.add_widget(
                input_field
            )


        scroll.add_widget(
            form
        )

        self.content.add_widget(
            scroll
        )


        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(70),
            spacing=dp(10)
        )


        save = Button(
            text="SPEICHERN",
            font_size="22sp",
            background_color=GREEN
        )

        save.bind(
            on_release=self.save_tractor
        )

        buttons.add_widget(
            save
        )


        cancel = Button(
            text="ABBRECHEN",
            font_size="22sp"
        )

        cancel.bind(
            on_release=self.show_tractor_list
        )

        buttons.add_widget(
            cancel
        )


        self.content.add_widget(
            buttons
        )


    # ========================================================
    # ANBAUGERÄT FORMULAR
    # ========================================================

    def build_implement_form(
        self,
        data=None
    ):

        self.hide_keyboard()

        self.clear_content()

        self.inputs = {}


        self.content.add_widget(
            make_label(
                text="ANBAUGERÄT",
                font_size="27sp",
                bold=True
            )
        )


        scroll = ScrollView(
            do_scroll_x=False
        )


        form = GridLayout(
            cols=2,
            spacing=dp(12),
            padding=dp(10),
            size_hint_y=None
        )

        form.bind(
            minimum_height=form.setter(
                "height"
            )
        )


        fields = [
            ("name", "Bezeichnung", False),
            ("manufacturer", "Hersteller", False),
            ("model", "Modell", False),
            ("type", "Typ", False),
            ("length", "Länge [m]", True),
            ("width", "Breite [m]", True),
            ("height", "Höhe [m]", True),
            ("working_width", "Arbeitsbreite [m]", True),
            (
                "distance_to_tractor",
                "Abstand zum Traktor [m]",
                True
            ),
            ("weight", "Gewicht [kg]", True),
            ("notes", "Notizen", False)
        ]


        for key, caption, numeric in fields:

            label = make_label(
                text=caption,
                font_size="20sp"
            )

            label.size_hint_y = None
            label.height = dp(
                110
                if key == "notes"
                else 65
            )

            form.add_widget(
                label
            )


            value = ""

            if data is not None:

                if data[key] is not None:

                    value = str(
                        data[key]
                    )


            input_field = self.create_input(
                key=key,
                value=value,
                numeric=numeric,
                multiline=(
                    key == "notes"
                )
            )


            form.add_widget(
                input_field
            )


        scroll.add_widget(
            form
        )

        self.content.add_widget(
            scroll
        )


        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(70),
            spacing=dp(10)
        )


        save = Button(
            text="SPEICHERN",
            font_size="22sp",
            background_color=GREEN
        )

        save.bind(
            on_release=self.save_implement
        )

        buttons.add_widget(
            save
        )


        cancel = Button(
            text="ABBRECHEN",
            font_size="22sp"
        )

        cancel.bind(
            on_release=self.show_implement_list
        )

        buttons.add_widget(
            cancel
        )


        self.content.add_widget(
            buttons
        )


    # ========================================================
    # TRAKTOR SPEICHERN
    # ========================================================

    def save_tractor(
        self,
        instance
    ):

        self.hide_keyboard()


        name = self.inputs["name"].text.strip()

        if not name:

            print(
                "Traktor benötigt eine Bezeichnung.",
                flush=True
            )

            return


        def value(key):

            text = (
                self.inputs[key]
                .text
                .strip()
            )

            return text or None


        def number(key):

            text = value(key)

            if text is None:

                return None

            try:

                return float(
                    text.replace(",", ".")
                )

            except ValueError:

                return None


        year = value("year")

        if year:

            try:

                year = int(year)

            except ValueError:

                year = None


        tractor_id = (
            self.database.add_tractor(

                name=name,

                manufacturer=(
                    self.inputs[
                        "manufacturer"
                    ].text.strip()
                ),

                model=(
                    self.inputs[
                        "model"
                    ].text.strip()
                ),

                year=year,

                length=number("length"),

                width=number("width"),

                height=number("height"),

                wheelbase=number(
                    "wheelbase"
                ),

                front_track=number(
                    "front_track"
                ),

                rear_track=number(
                    "rear_track"
                ),

                weight=number("weight"),

                notes=(
                    self.inputs[
                        "notes"
                    ].text.strip()
                )
            )
        )


        print(
            f"Traktor gespeichert: "
            f"{tractor_id}",
            flush=True
        )


        self.show_tractor_list()


    # ========================================================
    # ANBAUGERÄT SPEICHERN
    # ========================================================

    def save_implement(
        self,
        instance
    ):

        self.hide_keyboard()


        name = self.inputs["name"].text.strip()

        if not name:

            print(
                "Anbaugerät benötigt eine "
                "Bezeichnung.",
                flush=True
            )

            return


        def value(key):

            text = (
                self.inputs[key]
                .text
                .strip()
            )

            return text or None


        def number(key):

            text = value(key)

            if text is None:

                return None

            try:

                return float(
                    text.replace(",", ".")
                )

            except ValueError:

                return None


        implement_id = (
            self.database.add_implement(

                name=name,

                manufacturer=(
                    self.inputs[
                        "manufacturer"
                    ].text.strip()
                ),

                model=(
                    self.inputs[
                        "model"
                    ].text.strip()
                ),

                type=(
                    self.inputs[
                        "type"
                    ].text.strip()
                ),

                length=number("length"),

                width=number("width"),

                height=number("height"),

                working_width=number(
                    "working_width"
                ),

                distance_to_tractor=number(
                    "distance_to_tractor"
                ),

                weight=number("weight"),

                notes=(
                    self.inputs[
                        "notes"
                    ].text.strip()
                )
            )
        )


        print(
            f"Anbaugerät gespeichert: "
            f"{implement_id}",
            flush=True
        )


        self.show_implement_list()


    # ========================================================
    # AUSWAHL
    # ========================================================

    def select_machine(
        self,
        machine_id
    ):

        self.selected_id = machine_id

        print(
            f"Maschine ausgewählt: "
            f"{machine_id}",
            flush=True
        )


    # ========================================================
    # LÖSCHEN
    # ========================================================

    def delete_selected(
        self,
        instance
    ):

        if self.selected_id is None:

            print(
                "Keine Maschine ausgewählt.",
                flush=True
            )

            return


        if self.current_type == "tractor":

            self.database.delete_tractor(
                self.selected_id
            )

            self.show_tractor_list()

        else:

            self.database.delete_implement(
                self.selected_id
            )

            self.show_implement_list()


        self.selected_id = None


    # ========================================================
    # CONTENT LEEREN
    # ========================================================

    def clear_content(self):

        self.hide_keyboard()

        self.content.clear_widgets()


    # ========================================================
    # ZURÜCK
    # ========================================================

    def go_back(
        self,
        instance
    ):

        self.hide_keyboard()

        print(
            "Zurück zum Dashboard",
            flush=True
        )

        self.app.show_dashboard()
