from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QMenu, QToolButton, QWidgetAction


class RefereeMenu(QToolButton):
    selectionChanged = pyqtSignal()

    def __init__(self, title="Controllore", parent=None):
        super().__init__(parent)
        self._title = title or "Controllore"
        self._boxes = {}
        menu = QMenu(self)

        for key, label in (
            ("tfidf", "TF-IDF e similarità coseno"),
            ("bm25", "BM25 e confronto dei passaggi"),
            ("temporale", "Andamento temporale e ripetizioni"),
            ("llm", "LLM as a Judge"),
        ):
            box = QCheckBox(label, menu)
            box.setStyleSheet("padding: 6px 12px;")

            action = QWidgetAction(menu)
            action.setDefaultWidget(box)
            menu.addAction(action)

            self._boxes[key] = box
            box.toggled.connect(self._refresh)

        self.setMenu(menu)
        self.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        self._refresh()

    def selected(self):
        return {
            key: box.isChecked()
            for key, box in self._boxes.items()
        }

    def setSelected(self, values):
        if isinstance(values, bool):
            values = {"llm": values}

        values = values or {}

        for key, box in self._boxes.items():
            box.setChecked(bool(values.get(key, False)))

        self._refresh()

    def setTitle(self, title):
        self._title = title or "Controllore"
        self._refresh()

    def _refresh(self, checked=False):
        count = sum(
            box.isChecked()
            for box in self._boxes.values()
        )
        self.setText(f"{self._title} ({count}/4)")
        self.selectionChanged.emit()