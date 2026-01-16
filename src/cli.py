import typer
from .app import run_research
from .utils.logging import setup_logging

app = typer.Typer()

@app.command()
def main(
    ticker: str = typer.Option(..., help="Stock ticker symbol (e.g. TSLA)"),
    horizon: str = typer.Option("1m", help="Investment horizon (1w, 1m, 3m, 1y)"),
    risk: str = typer.Option("normal", help="Risk profile (conservative, normal, aggressive)"),
):
    """
    Run the Market Research Orchestrator for a given ticker.
    """
    setup_logging()
    typer.echo(f"Starting research for {ticker}...")
    try:
        result_path = run_research(ticker, horizon, risk)
        typer.echo(f"Research complete! Results saved in: {result_path}")
    except Exception as e:
        typer.echo(f"Error occurred: {e}", err=True)
        raise e

if __name__ == "__main__":
    app()
