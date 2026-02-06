"""报告生成模块

职责：
- 生成电量数据可视化报告
- 使用 Plotly 创建交互式图表
- 输出 HTML 格式报告

遵循 SOLID 原则：
- 单一职责：只负责报告生成
- 开闭原则：可扩展支持不同报告格式
- 依赖倒置：依赖 ReportData 抽象模型
"""

from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader, select_autoescape
from plotly.subplots import make_subplots

from .exceptions import StorageError
from .logger import logger
from .models import ReportData


class HTMLReporter:
    """HTML 报告生成器

    使用 Plotly 生成交互式可视化报告，使用 Jinja2 渲染模板。
    """

    def __init__(self, output_dir: Path):
        """初始化报告生成器

        Args:
            output_dir: 报告输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 Jinja2 环境
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def generate(
        self,
        data: ReportData,
        filename: str | None = None,
    ) -> Path:
        """生成 HTML 报告

        Args:
            data: 报告数据
            filename: 输出文件名（不指定则自动生成）

        Returns:
            生成的报告文件路径

        Raises:
            StorageError: 报告生成失败
        """
        try:
            # 生成文件名
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"electricity_report_{timestamp}.html"

            output_path = self.output_dir / filename

            # 创建图表
            fig = self._create_charts(data)

            # 添加标题和样式
            title = f"电量监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            fig.update_layout(
                title={
                    "text": title,
                    "x": 0.5,
                    "xanchor": "center",
                    "font": {"size": 24},
                },
                showlegend=True,
                template="plotly_white",
                height=1200,  # 总高度
            )

            # 生成 HTML
            html = self._build_html(fig, data)

            # 写入文件
            output_path.write_text(html, encoding="utf-8")

            logger.info(f"报告已生成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            raise StorageError(f"生成报告失败: {e}") from e

    def _create_charts(self, data: ReportData) -> go.Figure:
        """创建图表

        Args:
            data: 报告数据

        Returns:
            Plotly 图表对象
        """
        # 按时间正序排列（用于绘图）
        records = sorted(data.records, key=lambda r: r.timestamp)

        timestamps = [r.timestamp for r in records]
        powers = [r.power for r in records]

        # 创建子图：3行1列
        fig = make_subplots(
            rows=3,
            cols=1,
            subplot_titles=(
                "电量趋势图",
                "日消耗量趋势",
                "电量分布直方图",
            ),
            vertical_spacing=0.1,
            row_heights=[0.4, 0.3, 0.3],
        )

        # 1. 电量趋势折线图
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=powers,
                mode="lines+markers",
                name="剩余电量",
                line={"color": "royalblue", "width": 2},
                marker={"size": 6},
                hovertemplate=(
                    "<b>时间:</b> %{x}<br><b>电量:</b> %{y:.2f} 度<extra></extra>"
                ),
            ),
            row=1,
            col=1,
        )

        # 添加阈值线（如果有统计信息）
        if "threshold" in data.metadata:
            threshold = float(data.metadata["threshold"])
            fig.add_hline(
                y=threshold,
                line_dash="dash",
                line_color="red",
                annotation_text=f"告警阈值 ({threshold} 度)",
                row=1,
                col=1,
            )

        # 2. 日消耗量趋势（计算相邻两点之间的差值）
        if len(records) >= 2:
            consumption_dates = []
            daily_consumption = []

            for i in range(1, len(records)):
                prev_record = records[i - 1]
                curr_record = records[i]

                # 计算时间差（天）
                time_diff = (
                    curr_record.timestamp - prev_record.timestamp
                ).total_seconds() / 86400

                if time_diff > 0:
                    # 计算消耗（注意是减少）
                    consumption = (prev_record.power - curr_record.power) / time_diff

                    consumption_dates.append(curr_record.timestamp)
                    daily_consumption.append(abs(consumption))

            fig.add_trace(
                go.Bar(
                    x=consumption_dates,
                    y=daily_consumption,
                    name="日均消耗",
                    marker_color="lightcoral",
                    hovertemplate=(
                        "<b>日期:</b> %{x}<br>"
                        "<b>日均消耗:</b> %{y:.2f} 度/天<extra></extra>"
                    ),
                ),
                row=2,
                col=1,
            )

        # 3. 电量分布直方图
        fig.add_trace(
            go.Histogram(
                x=powers,
                name="电量分布",
                nbinsx=20,
                marker_color="lightseagreen",
                hovertemplate=(
                    "<b>电量范围:</b> %{x}<br><b>次数:</b> %{y}<extra></extra>"
                ),
            ),
            row=3,
            col=1,
        )

        # 更新坐标轴标签
        fig.update_xaxes(title_text="时间", row=1, col=1)
        fig.update_yaxes(title_text="电量 (度)", row=1, col=1)

        fig.update_xaxes(title_text="日期", row=2, col=1)
        fig.update_yaxes(title_text="消耗 (度/天)", row=2, col=1)

        fig.update_xaxes(title_text="电量 (度)", row=3, col=1)
        fig.update_yaxes(title_text="频次", row=3, col=1)

        return fig

    def _build_html(self, fig: go.Figure, data: ReportData) -> str:
        """构建完整的 HTML 报告

        Args:
            fig: Plotly 图表对象
            data: 报告数据

        Returns:
            HTML 字符串
        """
        # 获取图表 HTML（不包含完整的 HTML 结构）
        chart_html = fig.to_html(
            include_plotlyjs="cdn",
            full_html=False,
            config={"responsive": True},
        )

        # 准备模板数据
        threshold = float(data.metadata.get("threshold", "30"))

        template_data = {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "plotly_html": chart_html,
            "statistics": data.statistics,
            "threshold": threshold,
            "metadata": self._format_metadata_dict(data.metadata),
        }

        # 渲染模板
        template = self.jinja_env.get_template("report.html")
        return template.render(**template_data)

    def _format_metadata_dict(self, metadata: dict) -> dict:
        """格式化元数据为显示友好的字典

        Args:
            metadata: 元数据字典

        Returns:
            格式化后的字典
        """
        formatted = {}
        for key, value in metadata.items():
            if key == "threshold":
                formatted["告警阈值"] = f"{value} 度"
            elif key == "analysis_period":
                formatted["分析周期"] = f"最近 {value} 天"
            else:
                formatted[key] = value
        return formatted
