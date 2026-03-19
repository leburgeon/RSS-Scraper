""" Script to generate the HTML report for the newsletter using 
defined metrics for mention volume, sentiment distribution and share of voice. 
Compatible for lambda function too"""

import logging
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

from metrics import (
    recent_dates,
    retrieve_dynamodb_table,
    mentions_dataframe_creation,
    compute_mention_volume,
    sentiment_distribution_calculate,
    share_of_voice_calculate,
    mention_items_for_dates,
    top_3_rows,
    bottom_3_rows,
)

logging.basicConfig(level=logging.INFO)


def format_metric_value(value: float, metric_type: str) -> str:
    """Format metric values for display in the report."""
    if metric_type == "mention_volume":
        return str(int(value))

    if metric_type in ["positive_pct", "negative_pct", "share_of_voice"]:
        return f"{round(value * 100, 2)}%"

    return str(value)


def build_metric_table(df: pd.DataFrame, metric_column: str) -> pd.DataFrame:
    """Simple df with company name and metric to include in report"""

    mapping = {
        "mention_volume": "Mention Volume",
        "positive_pct": "Positive Sentiment",
        "share_of_voice": "Share of Voice",
    }

    metric_table_df = df[["entity_name", metric_column]].copy()

    metric_table_df[metric_column] = metric_table_df[metric_column].apply(
        lambda value: format_metric_value(value, metric_column)
    )
    metric_table_df["Company Name"] = metric_table_df["entity_name"]

    metric_table_df = metric_table_df[["Company Name", metric_column]].rename(
        columns={metric_column: mapping[metric_column]}
    )

    return metric_table_df


def build_sentiment_bar_chart(
        sentiment_df: pd.DataFrame,
        title: str,
        include_plotlyjs: str = "cdn",) -> str:
    """Grouped bar chart for company sentiment counts."""

    if sentiment_df.empty:
        return f"""
        <section class="card full-width">
            <h2>{title}</h2>
            <p>No data available.</p>
        </section>
        """

    company_names = sentiment_df["entity_name"].tolist()
    positive_values = sentiment_df["positive"].tolist()
    neutral_values = sentiment_df["neutral"].tolist()
    negative_values = sentiment_df["negative"].tolist()

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Positive",
            x=company_names,
            y=positive_values,
            text=positive_values,
            textposition="outside",
            marker_color="limegreen"
        )
    )

    fig.add_trace(
        go.Bar(
            name="Neutral",
            x=company_names,
            y=neutral_values,
            text=neutral_values,
            textposition="outside",
            marker_color="blue"
        )
    )

    fig.add_trace(
        go.Bar(
            name="Negative",
            x=company_names,
            y=negative_values,
            text=negative_values,
            textposition="outside",
            marker_color="red"
        )
    )

    for index in range(len(company_names) - 1):
        fig.add_vline(
            x=index + 0.5,
            line_width=1,
            line_dash="dash",
            line_color="gray",
            opacity=0.6
        )

    fig.update_layout(
        barmode="group",
        title=title,
        xaxis_title="Company Name",
        yaxis_title="Sentiment Count",
        margin={"l": 40, "r": 20, "t": 60, "b": 40},
        height=450,
        template="plotly_white",
        legend_title="Sentiment",
    )

    chart_html = fig.to_html(
        full_html=False,
        include_plotlyjs=include_plotlyjs,
        config={"displayModeBar": False},
    )

    return f"""
    <section class="card full-width">
        {chart_html}
    </section>
    """


def dataframe_to_html_table(df: pd.DataFrame, title: str, subheading: str) -> str:
    """Convert a DataFrame into a styled HTML table."""
    if df.empty:
        return f"""
        <section class="card">
            <h2>{title}</h2>
            <p>No data available.</p>
        </section>
        """

    table_html = df.to_html(index=False, classes="report-table", border=0)

    return f"""
    <section class="card">
        <h2>{title}</h2>
        <h3>{subheading}</h3>
        {table_html}
    </section>
    """


def build_html_report(
    report_date,
    top_mention_volume_table,
    top_sentiment_chart_html,
    top_share_of_voice_table,
    bottom_mention_volume_table,
    bottom_sentiment_chart_html,
    bottom_share_of_voice_table,
):
    """Build the full HTML report."""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Daily Media Report - {report_date}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 24px;
                background-color: #f7f7f7;
                color: #222;
            }}
            h1 {{
                margin-bottom: 8px;
            }}
            .subtitle {{
                color: #666;
                margin-bottom: 24px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }}
            .card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            }}
            .full-width {{
                grid-column: 1 / -1;
            }}
            .report-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 12px;
            }}
            .report-table th,
            .report-table td {{
                border: 1px solid #dddddd;
                padding: 10px;
                text-align: left;
            }}
            .report-table th {{
                background-color: #f0f0f0;
            }}
            h2 {{
                margin-top: 0;
            }}
            .section-heading {{
                margin-bottom: 0;
            }}
        </style>
    </head>
    <body>
        <h1>Daily Media Report</h1>
        <p class="subtitle">Report date: {report_date}</p>

        <div class="grid">
            <section class="card full-width">
                <h2 class="section-heading"><u>Top 3 Companies</u></h2>
            </section>

            {dataframe_to_html_table(top_mention_volume_table, "Mention Volume",
                                     subheading="Companies appearing in the most unique articles in this date range")}

            {dataframe_to_html_table(top_share_of_voice_table, "Share of Voice",
                                         subheading="Companies most discussed across all mentions in this date range")}
            {top_sentiment_chart_html}

            <section class="card full-width">
                <h2 class="section-heading"><u>Bottom 3 Companies</u></h2>
            </section>

            {dataframe_to_html_table(bottom_mention_volume_table, "Mention Volume",
                                             subheading="Companies appearing in the fewest unique articles in this date range")}
            {dataframe_to_html_table(bottom_share_of_voice_table, "Share of Voice",
                                                 subheading="Companies least discussed across all mentions in this date range")}
            {bottom_sentiment_chart_html}
        </div>
    </body>
    </html>
    """
    return html


def save_html_report(html_content: str, output_path: str):
    """Save the HTML report to a file."""
    Path(output_path).write_text(html_content, encoding="utf-8")
    logging.info("Saved HTML report to %s", output_path)


def generate_report_html(table_name: str, region_name: str) -> str:
    """Run the report pipeline and return the HTML string."""
    article_dates = recent_dates(2)
    report_date = f"{article_dates[0]} to {article_dates[-1]}"
    logging.info("Generating HTML report for %s", report_date)

    table = retrieve_dynamodb_table(table_name, region_name)
    items = mention_items_for_dates(table, article_dates)

    if not items:
        logging.info("No mention items found for the selected date range")
        return f"""
        <html>
            <body>
                <h1>Daily Media Report</h1>
                <p>Report date: {report_date}</p>
                <p>No data available for this date range.</p>
            </body>
        </html>
        """

    df = mentions_dataframe_creation(items)

    mention_volume_df = compute_mention_volume(df)
    sentiment_distribution_df = sentiment_distribution_calculate(df)
    share_of_voice_df = share_of_voice_calculate(df)
    top_mention_volume_df = top_3_rows(mention_volume_df, "mention_volume")

    bottom_mention_volume_df = bottom_3_rows(
        mention_volume_df[mention_volume_df["mention_volume"] >= 5], "mention_volume")
    # filter mention volume for bottom companies to those with at least 5 mentions to avoid outliers

    top_sentiment_df = top_3_rows(
        sentiment_distribution_df, "positive")
    bottom_sentiment_df = top_3_rows(
        sentiment_distribution_df, "negative")

    top_share_of_voice_df = top_3_rows(
        share_of_voice_df, "share_of_voice")

    bottom_share_of_voice_df = bottom_3_rows(
        share_of_voice_df[share_of_voice_df["share_of_voice"] >= 0.02], "share_of_voice")

    top_mention_volume_table = build_metric_table(
        top_mention_volume_df, "mention_volume")

    bottom_mention_volume_table = build_metric_table(
        bottom_mention_volume_df, "mention_volume")

    top_share_of_voice_table = build_metric_table(
        top_share_of_voice_df, "share_of_voice")

    bottom_share_of_voice_table = build_metric_table(
        bottom_share_of_voice_df, "share_of_voice")

    top_sentiment_chart_html = build_sentiment_bar_chart(
        top_sentiment_df, f"Companies most positively talked about in date range {report_date}")

    bottom_sentiment_chart_html = build_sentiment_bar_chart(
        bottom_sentiment_df,
        f"Companies most negatively talked about companies in date range {report_date}",
        include_plotlyjs=False,
    )

    html_report = build_html_report(
        report_date=report_date,
        top_mention_volume_table=top_mention_volume_table,
        top_sentiment_chart_html=top_sentiment_chart_html,
        top_share_of_voice_table=top_share_of_voice_table,
        bottom_mention_volume_table=bottom_mention_volume_table,
        bottom_sentiment_chart_html=bottom_sentiment_chart_html,
        bottom_share_of_voice_table=bottom_share_of_voice_table,
    )

    return html_report


def lambda_handler(event, context):
    """Returns the HTML report in the response body for the Lambda function."""

    table_name = "c22_charlie_media_mvp"
    region_name = "eu-west-2"

    html_report = generate_report_html(table_name, region_name)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html"
        },
        "body": html_report
    }


def main():
    """Main function to generate and save the HTML report locally."""

    table_name = "c22-rss-scraper-table"
    region_name = "eu-west-2"

    html_report = generate_report_html(table_name, region_name)
    save_html_report(html_report, "daily_media_report.html")


if __name__ == "__main__":
    main()
