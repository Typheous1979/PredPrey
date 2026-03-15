from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser,
    QPushButton, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt
from analysis.analyzer import AnalysisResult


_OUTCOME_COLORS = {
    "Coexistence":        "#2ecc71",
    "Prey Dominance":     "#4169e1",
    "Predator Dominance": "#dc322f",
    "Ecosystem Collapse": "#888888",
}

_SECTION_STYLE = "font-size:13px; font-weight:bold; color:#cccccc; margin-top:8px;"
_STAT_STYLE    = "font-size:11px; color:#aaaaaa;"


class AnalysisDialog(QDialog):
    def __init__(self, result: AnalysisResult, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Run #{result.run_id} — Analysis Report")
        self.resize(680, 780)
        self._build_ui(result)

    def _build_ui(self, r: AnalysisResult):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # ── Header ─────────────────────────────────────────────────────
        color = _OUTCOME_COLORS.get(r.outcome, "#ffffff")
        header = QLabel(
            f"<span style='font-size:16px; font-weight:bold;'>Run #{r.run_id}</span>"
            f"&nbsp;&nbsp;&nbsp;"
            f"<span style='font-size:15px; font-weight:bold; color:{color};'>{r.outcome}</span>"
            f"<span style='font-size:11px; color:#888;'>&nbsp;— {r.total_ticks} ticks</span>"
        )
        header.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(header)

        # ── Stats grid ─────────────────────────────────────────────────
        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.Shape.StyledPanel)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(16)

        def stat_col(lines: list[tuple[str, str]]) -> QLabel:
            html = "".join(
                f"<b style='color:#cccccc'>{k}</b><br>"
                f"<span style='color:#ffffff; font-size:13px'>{v}</span><br><br>"
                for k, v in lines
            )
            lbl = QLabel(html)
            lbl.setTextFormat(Qt.TextFormat.RichText)
            lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
            return lbl

        osc_str = r.oscillation or "No clear cycle"
        trend_str = (
            f"Prey {r.prey_late_trend.lower()} · "
            f"Predators {r.predator_late_trend.lower()} · "
            f"Plants {r.plant_late_trend.lower()}"
        )
        stats_layout.addWidget(stat_col([
            ("Peak Prey",       str(r.peak_prey)),
            ("Mean Prey",       str(r.mean_prey)),
            ("Prey Stability",  r.prey_stability),
        ]))
        stats_layout.addWidget(stat_col([
            ("Peak Predators",  str(r.peak_predators)),
            ("Mean Predators",  str(r.mean_predators)),
            ("Oscillation",     osc_str),
        ]))
        stats_layout.addWidget(stat_col([
            ("Mean Plants",     str(r.mean_plants)),
            ("Prey Extinctions",  str(r.prey_extinctions)),
            ("Pred Extinctions",  str(r.pred_extinctions)),
        ]))
        stats_layout.addWidget(stat_col([
            ("Late-Run Trends", trend_str),
        ]))
        layout.addWidget(stats_frame)

        # ── Narrative sections ─────────────────────────────────────────
        report_html = self._build_html(r)
        browser = QTextBrowser()
        browser.setHtml(report_html)
        browser.setOpenExternalLinks(False)
        browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(browser)

        # ── Close button ───────────────────────────────────────────────
        btn_close = QPushButton("Close")
        btn_close.setFixedHeight(28)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

    @staticmethod
    def _build_html(r: AnalysisResult) -> str:
        def section(title: str, icon: str, text: str, color: str = "#cccccc") -> str:
            return f"""
            <p style='margin-top:14px; margin-bottom:2px;'>
              <span style='font-size:13px; font-weight:bold; color:{color};'>{icon} {title}</span>
            </p>
            <p style='font-size:12px; color:#dddddd; line-height:1.5; margin:0;'>{text}</p>
            <hr style='border:0; border-top:1px solid #333; margin-top:10px;'>
            """

        return f"""
        <html><body style='background:#1e1e1e; color:#dddddd; font-family:Segoe UI, Arial, sans-serif;'>
        {section("Predator Hunting Strategy", "&#128481;", r.hunting_strategy,   "#dc322f")}
        {section("Prey Evasion Strategy",     "&#128007;", r.evasion_strategy,   "#4169e1")}
        {section("Plant &amp; Environment",   "&#127807;", r.plant_environment,  "#228b22")}
        {section("Run Outcome",               "&#9654;",   r.final_outcome,      "#f0c040")}
        {section("Overall Assessment",        "&#128202;", r.overall_assessment, "#aaaaaa")}
        </body></html>
        """
