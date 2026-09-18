"""
Главный файл запуска приложения
"""

import click
import uvicorn
from rich.console import Console
from core.database import init_db

console = Console()


@click.group()
def cli():
    """College Management System"""
    pass


@cli.command()
def init():
    """Инициализировать базу данных"""
    console.print("[bold blue]Инициализация БД...[/bold blue]")
    init_db()
    console.print("[bold green]✅ Готово![/bold green]")


@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True)
@click.option("--reload", is_flag=True, default=False, help="Автоперезапуск при изменении кода")
def run(host: str, port: int, reload: bool):
    """Запустить API-сервер (FastAPI + uvicorn)"""
    console.print(f"[green]Запуск API на http://{host}:{port} ...[/green]")
    uvicorn.run("core.api:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    cli()
