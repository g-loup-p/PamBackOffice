import logging
import flet as ft

class ListBoxHandler(logging.Handler):
    """
    Handler de logging personnalisé pour afficher les logs 
    dans une ListView Flet.
    """
    def __init__(self, list_view_control, page):
        super().__init__()
        self.list_view = list_view_control
        self.page = page

    def emit(self, record):
        try:
            log_entry = self.format(record)
            
            # Définition des couleurs selon le niveau de log
            color = ft.Colors.WHITE
            if record.levelno == logging.INFO:
                color = ft.Colors.GREEN_400
            elif record.levelno == logging.WARNING:
                color = ft.Colors.YELLOW_400
            elif record.levelno >= logging.ERROR:
                color = ft.Colors.RED_400

            self.list_view.controls.append(
                ft.Text(f"{log_entry}", color=color, font_family="Consolas", size=12)
            )
            
            # Rotation des logs : garde les 100 dernières lignes
            if len(self.list_view.controls) > 100:
                self.list_view.controls.pop(0)
                
            self.page.update()
        except Exception:
            # Évite de faire planter l'app si le log échoue
            self.handleError(record)