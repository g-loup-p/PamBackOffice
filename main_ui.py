import json
import time
import threading
import logging
import os
import webbrowser
import platform
import subprocess

# Third-party imports
import flet as ft

# Local imports
import pipeline
import ui_logger
import ytprocess
import rss_manager

# --- CONFIGURATION ---
CONFIG_FILE = "config.json"
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- THEME MANAGER ---
class AppPalette:
    def __init__(self):
        self.mode = "dark"
        self.bg = ""
        self.surface = ""
        self.video_tile = ""
        self.surface_hover = ""
        self.text = ""
        self.subtext = ""
        self.divider = ""
        self.input_bg = ""
        self.red = ""
        self.warning = ""
        self.accent_blue = ""
        self.update_colors()

    def update_colors(self):
        if self.mode == "dark":
            self.bg = "#0F0F0F"
            self.surface = "#272727"
            self.video_tile = "#1A1A1A"
            self.surface_hover = "#3F3F3F"
            self.text = "#FFFFFF"
            self.subtext = "#AAAAAA"
            self.divider = "#303030"
            self.input_bg = "#121212"
            self.red = "#FF0000"
            self.warning = "#E8A209"
            self.accent_blue = "#0101A8"
        else:
            self.bg = "#F9F9F9"
            self.surface = "#FFFFFF"
            self.video_tile = "#F0F0F0"
            self.surface_hover = "#E5E5E5"
            self.text = "#0F0F0F"
            self.subtext = "#606060"
            self.divider = "#E5E5E5"
            self.input_bg = "#F0F0F0"
            self.red = "#FF0000"
            self.warning = "#E8A209"
            self.accent_blue = "#0101A8"

palette = AppPalette()

# --- CONFIG UTILS ---
def load_config():
    default_config = {
        "watch_frequency_seconds": 60, 
        "rss_fetch_limit": 15,
        "xml_watch_folder": "MEDIA", 
        "rss_channels": []
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                # Merge avec default pour éviter les clés manquantes
                for key, val in default_config.items():
                    if key not in data:
                        data[key] = val
                return data
        except Exception as e:
            logger.error(f"Erreur lecture config: {e}")
    return default_config

def save_config(cfg):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(cfg, f, indent=4)
    except Exception as e:
        logger.error(f"Erreur sauvegarde config: {e}")

# --- MAIN APP ---
def main(page: ft.Page):
    # Setup Page
    page.title = "Pam BackOffice"
    page.window_icon = "assets/icon.png"
    page.padding = 0
    page.window_width = 1280
    page.window_height = 850
    
    # Fonts
    page.fonts = {
        "YoutubeSansBold": "fonts/youtube-sans-bold.ttf",
        "YoutubeSansMedium": "fonts/youtube-sans-medium.ttf",
        "YoutubeSansLight": "fonts/youtube-sans-light.ttf"
    }
    page.theme = ft.Theme(font_family="YoutubeSansMedium")
    
    config = load_config()
    is_running = False
    channels_metadata = {} 

    # --- HELPERS ---
    def open_file_externally(path):
        if not os.path.exists(path):
            return
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.call(("open", path))
            else:
                subprocess.call(("xdg-open", path))
        except Exception as ex:
            logger.error(f"Erreur ouverture fichier {path}: {ex}")

    # --- FILE PICKER ---
    def on_folder_result(e: ft.FilePickerResultEvent):
        if e.path:
            txt_path.value = e.path
            txt_path.update()
            
    folder_picker = ft.FilePicker(on_result=on_folder_result)
    page.overlay.append(folder_picker)

    # --- THEME SWITCHING ---
    def apply_theme():
        palette.update_colors()
        page.bgcolor = palette.bg
        page.theme_mode = ft.ThemeMode.DARK if palette.mode == "dark" else ft.ThemeMode.LIGHT
        
        img_logo.src = "assets/logo_dark.svg" if palette.mode == "dark" else "assets/logo_light.svg"
        top_bar.bgcolor = palette.bg
        
        # Search Bar
        search_container.bgcolor = palette.input_bg
        search_container.border = ft.border.all(1, palette.divider)
        txt_manual_url.text_style = ft.TextStyle(font_family="YoutubeSansMedium", color=palette.text)
        txt_manual_url.hint_style = ft.TextStyle(color=palette.subtext, font_family="YoutubeSansLight")
        btn_manual_send.icon_color = palette.text
        
        # Logs
        logs_container.bgcolor = palette.surface
        logs_container.border = ft.border.all(1, palette.divider)
        
        # Rail
        rail.bgcolor = palette.bg
        rail.indicator_color = palette.surface

        # Inputs généraux
        try:
            inputs = [txt_freq, txt_rss_limit, txt_path, txt_new_channel]
            for inp in inputs:
                inp.bgcolor = palette.input_bg
                inp.border_color = palette.divider
                inp.text_style = ft.TextStyle(color=palette.text)
                inp.label_style = ft.TextStyle(color=palette.subtext)
            
            btn_subscribe.bgcolor = palette.text
            txt_subscribe.color = palette.bg
        except NameError:
            pass # Controls not initialized yet

        btn_pick_folder.icon_color = palette.text
        try:
            btn_open_config.icon_color = palette.subtext
        except NameError: pass

        icon_pamtube_large.color = palette.red

        if palette.mode == "dark":
            btn_open_pamtube.bgcolor = palette.text 
            txt_open_pamtube.color = palette.bg 
            btn_open_pamtube.content.controls[0].color = palette.bg
            btn_open_pamtube.border = None
        else:
            btn_open_pamtube.bgcolor = palette.input_bg 
            txt_open_pamtube.color = palette.text 
            btn_open_pamtube.content.controls[0].color = palette.text
            btn_open_pamtube.border = ft.border.all(1, palette.divider)

        status_indicator.bgcolor = palette.surface
        
        if not is_running:
            btn_run.bgcolor = palette.text
            btn_run.content.controls[0].color = palette.bg 
            btn_run.content.controls[1].color = palette.bg 
            status_text.color = palette.subtext
        else:
            btn_run.bgcolor = palette.red
            btn_run.content.controls[0].color = "#FFFFFF"
            btn_run.content.controls[1].color = "#FFFFFF"

        btn_open_logs.icon_color = palette.subtext

        if rail.selected_index == 1:
            refresh_channels_ui()
            
        page.update()

    def toggle_theme_mode(e):
        palette.mode = "light" if palette.mode == "dark" else "dark"
        icon_btn_theme.icon = ft.Icons.DARK_MODE if palette.mode == "dark" else ft.Icons.LIGHT_MODE
        apply_theme()

    # --- LOGGING SETUP ---
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        file_handler = logging.FileHandler("pam_backoffice.log", mode="a", encoding="utf-8")
        file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    logs_view = ft.ListView(expand=True, spacing=2, auto_scroll=True)
    handler = ui_logger.ListBoxHandler(logs_view, page)
    formatter = logging.Formatter('%(asctime)s • %(message)s', datefmt='%H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # --- BACKGROUND WORKER ---
    status_dot = ft.Container(width=8, height=8, bgcolor=palette.red, border_radius=10)
    status_text = ft.Text("ÉTEINT", color=palette.subtext, size=12, font_family="YoutubeSansBold")
    
    status_indicator = ft.Container(
        content=ft.Row([status_dot, status_text], spacing=6),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        border_radius=20,
        bgcolor=palette.surface
    )

    def background_loop():
        nonlocal is_running
        while is_running:
            try:
                # Reload config dynamically
                current_freq = int(config.get("watch_frequency_seconds", 60))
                current_rss_limit = int(config.get("rss_fetch_limit", 15))
                current_xml_path = config.get("xml_watch_folder", "MEDIA")
                current_channels = config.get("rss_channels", [])
                
                check_state = lambda: is_running

                pipeline.run_rss_check(current_channels, limit=current_rss_limit, is_running_callback=check_state)
                if not is_running: break

                pipeline.run_batch_xml(current_xml_path, is_running_callback=check_state)
                if not is_running: break
                
                logger.info(f"💤 Pause de {current_freq}s...")
                
                # Sleep with check
                for _ in range(current_freq):
                    if not is_running: break
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Erreur Loop: {e}")
                time.sleep(5)

    def toggle_monitoring(e):
        nonlocal is_running
        if not is_running:
            is_running = True
            # Visual update ON
            btn_run.content.controls[0].name = ft.Icons.STOP_CIRCLE_OUTLINED
            btn_run.content.controls[1].value = "ARRÊTER"
            btn_run.bgcolor = palette.red 
            btn_run.content.controls[1].color = "#FFFFFF" 
            btn_run.content.controls[0].color = "#FFFFFF"
            status_dot.bgcolor = ft.Colors.GREEN
            status_text.value = "ACTIF"
            status_indicator.update()
            btn_run.update()
            
            threading.Thread(target=background_loop, daemon=True).start()
            logger.info("🚀 Monitoring démarré.")
        else:
            is_running = False
            # Visual update OFF
            btn_run.content.controls[0].name = ft.Icons.PLAY_CIRCLE_FILLED
            btn_run.content.controls[1].value = "LANCER"
            btn_run.bgcolor = palette.text 
            btn_run.content.controls[1].color = palette.bg
            btn_run.content.controls[0].color = palette.bg
            status_dot.bgcolor = palette.red
            status_text.value = "ÉTEINT"
            status_text.color = palette.subtext
            status_indicator.update()
            btn_run.update()
            logger.info("🛑 Arrêt demandé...")

    # --- MANUAL SEARCH UI ---
    def run_manual_download(url):
        success, msg = pipeline.process_single_url(url, source_type="MANUEL")
        if success:
            page.snack_bar = ft.SnackBar(ft.Text(f"✅ Succès : {msg}"), bgcolor="#2BA640")
        else:
            page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erreur : {msg}"), bgcolor=palette.red)
        page.snack_bar.open = True
        txt_manual_url.disabled = False
        btn_manual_send.disabled = False
        txt_manual_url.value = ""
        page.update()

    def on_manual_click(e):
        if not txt_manual_url.value: return
        url = txt_manual_url.value
        logger.info(f"👉 Demande manuelle : {url}")
        txt_manual_url.disabled = True
        btn_manual_send.disabled = True
        page.update()
        threading.Thread(target=run_manual_download, args=(url,), daemon=True).start()

    txt_manual_url = ft.TextField(
        hint_text="Coller une URL Youtube",
        hint_style=ft.TextStyle(color=palette.subtext, font_family="YoutubeSansLight"),
        text_style=ft.TextStyle(font_family="YoutubeSansMedium", color=palette.text),
        border=ft.InputBorder.NONE,
        content_padding=ft.padding.only(left=15, bottom=12),
        expand=True,
        text_size=14,
        selection_color=palette.accent_blue,
        on_submit=on_manual_click
    )

    btn_manual_send = ft.IconButton(
        icon=ft.Icons.CLOUD_DOWNLOAD_OUTLINED, 
        icon_color=palette.text,
        bgcolor=ft.Colors.TRANSPARENT,
        on_click=on_manual_click,
        tooltip="Télécharger"
    )

    search_container = ft.Container(
        content=ft.Row([
            txt_manual_url,
            ft.Container(width=1, bgcolor=palette.divider, margin=ft.margin.symmetric(vertical=8)), 
            btn_manual_send
        ], spacing=0),
        bgcolor=palette.input_bg,
        border=ft.border.all(1, palette.divider),
        border_radius=40,
        width=550,
        height=40,
        padding=ft.padding.only(right=5)
    )

    # --- HEADER ELEMENTS ---
    icon_btn_theme = ft.IconButton(ft.Icons.DARK_MODE, on_click=toggle_theme_mode, tooltip="Changer le thème")
    img_logo = ft.Image(src="assets/logo_light.svg", width=32, height=32, fit=ft.ImageFit.CONTAIN)

    top_bar = ft.Container(
        bgcolor=palette.bg,
        padding=ft.padding.symmetric(horizontal=20, vertical=10),
        content=ft.Row([
            ft.Row([img_logo], width=200),
            ft.Container(content=search_container, alignment=ft.alignment.center, expand=True),
            ft.Row([status_indicator, icon_btn_theme], alignment=ft.MainAxisAlignment.END, width=200)
        ])
    )

    btn_run = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.PLAY_CIRCLE_FILLED, color=palette.bg),
            ft.Text("LANCER", color=palette.bg, font_family="YoutubeSansBold")
        ], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=palette.text, 
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        border_radius=18,
        on_click=toggle_monitoring,
        ink=True,
        width=140
    )

    btn_open_logs = ft.IconButton(
        icon=ft.Icons.OUTPUT_ROUNDED, 
        icon_color=palette.subtext,
        icon_size=18,
        tooltip="Ouvrir le fichier de logs",
        on_click=lambda _: open_file_externally("pam_backoffice.log")
    )

    logs_header = ft.Row([
        ft.Text("Logs du système:", font_family="YoutubeSansBold", size=16),
        btn_open_logs
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    logs_container = ft.Container(
        content=ft.Column([logs_header, ft.Divider(color=palette.divider), logs_view]),
        bgcolor=palette.surface,
        border_radius=12,
        padding=15,
        expand=True,
        border=ft.border.all(1, palette.divider)
    )

    dashboard_content = ft.Container(
        padding=20,
        content=ft.Column([
            ft.Text("Tableau de bord", size=24, font_family="YoutubeSansBold"),
            ft.Container(height=10),
            ft.Row([
                ft.Column([
                    ft.Text("Mode automatique:", font_family="YoutubeSansBold", size=18),
                    ft.Text("Gérez le monitoring RSS et le traitement XML.", color=palette.subtext, size=13),
                ], expand=True),
                btn_run
            ]),
            ft.Container(height=20),
            logs_container
        ], expand=True)
    )

    # --- CHANNELS PAGE ---
    channels_list_view = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)

    def confirm_delete_channel(channel_id, keep_history, dlg_instance):
        if channel_id in config["rss_channels"]:
            config["rss_channels"].remove(channel_id)
            save_config(config)
        
        if not keep_history:
            rss_manager.clear_channel_history(channel_id)
            logger.info(f"🗑️ Historique supprimé pour {channel_id}")
        else:
            logger.info(f"💾 Historique conservé pour {channel_id}")

        page.close(dlg_instance)
        refresh_channels_ui()
        logger.info(f"👁️‍🗨️ Abonnement retiré : {channel_id}")

    def show_delete_dialog(channel_id, channel_name):
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Supprimer l'abonnement ?"),
            content=ft.Text(
                f"Vous vous apprettez à supprimer l'abonnement à '{channel_name}' ?\n \n"
                "Que faire de l'historique des vidéos déjà téléchargées ?"
            ),
            actions_alignment=ft.MainAxisAlignment.END,
        )
        dlg.actions = [
            ft.TextButton("Annuler", on_click=lambda e: page.close(dlg)),
            ft.TextButton(
                "1. Tout supprimer", 
                style=ft.ButtonStyle(color=palette.red),
                on_click=lambda e: confirm_delete_channel(channel_id, False, dlg)
            ),
            ft.TextButton(
                "2. Garder l'historique",
                style=ft.ButtonStyle(color=palette.warning), 
                on_click=lambda e: confirm_delete_channel(channel_id, True, dlg)
            ),
        ]
        page.open(dlg)

    def delete_single_video(channel_id, video_id):
        if rss_manager.remove_video_from_history(channel_id, video_id):
            page.snack_bar = ft.SnackBar(ft.Text("Vidéo oubliée (sera retéléchargée au prochain scan)"), bgcolor=palette.accent_blue)
            page.snack_bar.open = True
            refresh_channels_ui()
            page.update()

    def build_history_view(channel_id):
        history = rss_manager.get_channel_history(channel_id)
        if not history:
            return ft.Container(content=ft.Text("Aucune vidéo traitée pour le moment.", size=12, color=palette.subtext), padding=10)

        video_rows = []
        for vid in reversed(history):
            row = ft.Container(
                bgcolor=palette.video_tile, 
                border_radius=8,
                padding=5,
                content=ft.Row([
                    ft.Image(
                        src=vid.get("thumb", "") or "https://placehold.co/60x45", 
                        width=60, height=45, 
                        fit=ft.ImageFit.COVER, 
                        border_radius=4
                    ),
                    ft.Column([
                        ft.Text(vid.get("title", "Inconnu")[:40]+"...", size=12, weight="bold", color=palette.text),
                        ft.Text(vid.get("id", ""), size=10, color=palette.subtext, font_family="Consolas")
                    ], spacing=2, expand=True),
                    ft.IconButton(
                        ft.Icons.REFRESH, 
                        tooltip="Oublier (Re-télécharger)", 
                        icon_size=16, 
                        icon_color=palette.text,
                        on_click=lambda e, cid=channel_id, vid=vid["id"]: delete_single_video(cid, vid)
                    )
                ])
            )
            video_rows.append(row)
        
        return ft.Container(
            height=350,
            content=ft.ListView(
                controls=video_rows, 
                spacing=5,
                padding=ft.padding.only(left=10, right=10, top=10, bottom=30)
            )
        )

    def refresh_channels_ui():
        channels_list_view.controls.clear()
        
        for ch_id in config["rss_channels"]:
            if ch_id not in channels_metadata:
                channels_metadata[ch_id] = {
                    "name": "Chargement...", 
                    "avatar": f"https://robohash.org/{ch_id}?set=set1"
                }
                def fetch_meta(cid):
                    name, avatar, _ = ytprocess.get_channel_infos(cid)
                    channels_metadata[cid] = {"name": name, "avatar": avatar}
                    refresh_channels_ui()
                threading.Thread(target=fetch_meta, args=(ch_id,), daemon=True).start()
            
            meta = channels_metadata[ch_id]
            history = rss_manager.get_channel_history(ch_id)
            count_videos = len(history)

            channels_list_view.controls.append(
                ft.Card(
                    color=palette.surface,
                    elevation=0,
                    content=ft.ExpansionTile(
                        leading=ft.CircleAvatar(foreground_image_src=meta["avatar"], radius=15),
                        title=ft.Text(f"{meta['name']} ({count_videos})", weight="bold", font_family="YoutubeSansMedium", size=14, color=palette.text),
                        subtitle=ft.Text(ch_id, color=palette.subtext, size=11, font_family="Consolas"),
                        icon_color=palette.text,
                        collapsed_icon_color=palette.subtext,
                        shape=ft.RoundedRectangleBorder(radius=0),
                        tile_padding=ft.padding.symmetric(horizontal=10),
                        controls=[
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                content=ft.Row([
                                    ft.Text("Historique des vidéos traitées", size=12, color=palette.text, weight="bold"),
                                    ft.Container(expand=True),
                                    ft.TextButton(
                                        "Supprimer la chaîne", 
                                        icon=ft.Icons.DELETE_FOREVER, 
                                        icon_color=palette.red,
                                        style=ft.ButtonStyle(color=palette.red),
                                        on_click=lambda e, x=ch_id, n=meta["name"]: show_delete_dialog(x, n)
                                    )
                                ])
                            ),
                            build_history_view(ch_id)
                        ]
                    )
                )
            )
        if channels_list_view.page:
            channels_list_view.update()

    def add_channel(e):
        val = txt_new_channel.value.strip()
        if not val: return
        txt_new_channel.disabled = True
        page.update()

        def process_add():
            name, avatar, real_id = ytprocess.get_channel_infos(val)
            if real_id and real_id not in config["rss_channels"]:
                config["rss_channels"].append(real_id)
                save_config(config)
                channels_metadata[real_id] = {"name": name, "avatar": avatar}
                logger.info(f"👁️‍🗨️ Abonnement ajouté : {name}")
            else:
                logger.warning("Chaîne déjà présente ou introuvable.")
            
            txt_new_channel.value = ""
            txt_new_channel.disabled = False
            refresh_channels_ui()
            page.update()

        threading.Thread(target=process_add, daemon=True).start()

    txt_new_channel = ft.TextField(
        label="URL ou ID de la chaîne", 
        label_style=ft.TextStyle(color=palette.subtext, size=12),
        bgcolor=palette.input_bg, 
        border_color=palette.divider,
        border_radius=4, text_size=14, height=40, expand=True,
        on_submit=add_channel
    )

    txt_subscribe = ft.Text("S'ABONNER", font_family="YoutubeSansBold", size=13, color=palette.bg)
    btn_subscribe = ft.Container(
        content=txt_subscribe,
        bgcolor=palette.text, 
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        border_radius=18,
        on_click=add_channel,
        ink=True
    )

    channels_content = ft.Container(
        padding=20,
        content=ft.Column([
            ft.Text("Abonnements", size=24, font_family="YoutubeSansBold"),
            ft.Container(height=10),
            ft.Row([txt_new_channel, btn_subscribe]), 
            ft.Divider(color=palette.divider, height=30),
            ft.Column([channels_list_view], expand=True, scroll=ft.ScrollMode.AUTO)
        ], expand=True)
    )

    # --- PAMTUBE PAGE ---
    def open_pamtube(e): 
        webbrowser.open("https://pamtube.netlify.app")
    
    icon_pamtube_large = ft.Icon(ft.Icons.ONDEMAND_VIDEO_ROUNDED, size=100)
    txt_open_pamtube = ft.Text("ACCÉDER À PAMTUBE", font_family="YoutubeSansBold", size=14)
    btn_open_pamtube = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.LANGUAGE), txt_open_pamtube], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
        padding=ft.padding.symmetric(horizontal=30, vertical=20),
        border_radius=30,
        on_click=open_pamtube,
        ink=True,
        width=250
    )

    pamtube_content = ft.Container(
        padding=20,
        alignment=ft.alignment.center,
        content=ft.Column([
            icon_pamtube_large,
            ft.Text("PamTube", size=40, font_family="YoutubeSansBold"),
            ft.Text("Retrouvez tous vos médias générés, sur la plateforme web.", size=16, color=palette.subtext),
            ft.Container(height=40),
            btn_open_pamtube
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

    # --- SETTINGS PAGE ---
    txt_freq = ft.TextField(
        label="Fréquence de vérification (sec)", 
        value=str(config.get("watch_frequency_seconds", 60)), 
        bgcolor=palette.input_bg, 
        border_radius=4
    )
    
    txt_rss_limit = ft.TextField(
        label="Profondeur d'analyse RSS (NB vidéos)", 
        value=str(config.get("rss_fetch_limit", 15)), 
        bgcolor=palette.input_bg, 
        border_radius=4,
        suffix_text=" (max 15)"
    )

    txt_path = ft.TextField(
        label="Dossier XML", 
        value=config.get("xml_watch_folder", "MEDIA"), 
        bgcolor=palette.input_bg, 
        border_radius=4,
        expand=True 
    )

    btn_pick_folder = ft.IconButton(
        icon=ft.Icons.DRIVE_FOLDER_UPLOAD_OUTLINED,
        icon_color=palette.text,
        tooltip="Choisir un dossier",
        on_click=lambda _: folder_picker.get_directory_path()
    )

    def save_settings(e):
        try:
            config["watch_frequency_seconds"] = int(txt_freq.value)
            config["rss_fetch_limit"] = int(txt_rss_limit.value) 
            config["xml_watch_folder"] = txt_path.value
            save_config(config)
            page.snack_bar = ft.SnackBar(ft.Text("Paramètres enregistrés et appliqués", color="white"), bgcolor="#2BA640")
            page.snack_bar.open = True
            page.update()
            logger.info(f"💾 Configuration mise à jour.")
        except Exception as ex:
            logger.error(f"Erreur config: {ex}")
            page.snack_bar = ft.SnackBar(ft.Text("Erreur dans les valeurs (nombres requis)", color="white"), bgcolor=palette.red)
            page.snack_bar.open = True
            page.update()

    btn_open_config = ft.IconButton(
        icon=ft.Icons.OUTPUT_ROUNDED, 
        icon_color=palette.subtext,
        tooltip="Ouvrir le fichier config.json",
        on_click=lambda _: open_file_externally(CONFIG_FILE)
    )

    settings_header = ft.Row([
        ft.Text("Paramètres", size=24, font_family="YoutubeSansBold"),
        btn_open_config
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    settings_content = ft.Container(
        padding=20,
        content=ft.Column([
            settings_header,
            ft.Divider(color=palette.divider, height=20),
            txt_freq,
            ft.Container(height=10),
            txt_rss_limit,
            ft.Container(height=10),
            ft.Row([txt_path, btn_pick_folder]),
            ft.Container(height=30),
            ft.Row([
                ft.Container(
                    content=ft.Text("ENREGISTRER", color="#FFFFFF", font_family="YoutubeSansBold"),
                    alignment=ft.alignment.center,
                    bgcolor=palette.accent_blue,
                    padding=10,
                    border_radius=4,
                    on_click=save_settings,
                    ink=True,
                    width=150
                )
            ])
        ])
    )

    # --- NAVIGATION ---
    body_container = ft.Container(content=dashboard_content, expand=True)

    def nav_change(e):
        idx = e.control.selected_index
        if idx == 0: 
            body_container.content = dashboard_content
        elif idx == 1: 
            refresh_channels_ui()
            body_container.content = channels_content
        elif idx == 2: 
            body_container.content = pamtube_content 
        elif idx == 3: 
            body_container.content = settings_content 
        body_container.update()

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=72,
        min_extended_width=200,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.DASHBOARD_OUTLINED, 
                selected_icon=ft.Icons.DASHBOARD, 
                label_content=ft.Text("Tableau de bord", font_family="YoutubeSansMedium", size=10)
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.VIDEO_LIBRARY_OUTLINED, 
                selected_icon=ft.Icons.VIDEO_LIBRARY, 
                label_content=ft.Text("Abonnements", font_family="YoutubeSansMedium", size=10)
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.LIBRARY_MUSIC_OUTLINED, 
                selected_icon=ft.Icons.LIBRARY_MUSIC, 
                label_content=ft.Text("PamTube", font_family="YoutubeSansMedium", size=10)
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED, 
                selected_icon=ft.Icons.SETTINGS, 
                label_content=ft.Text("Paramètres", font_family="YoutubeSansMedium", size=10)
            ),
        ],
        on_change=nav_change,
    )

    apply_theme()

    page.add(
        ft.Column([
            top_bar,
            ft.Divider(height=1, color=palette.divider),
            ft.Row([rail, body_container], expand=True)
        ], expand=True, spacing=0)
    )

if __name__ == "__main__":
    ft.app(target=main)