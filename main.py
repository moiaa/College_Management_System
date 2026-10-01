"""
Главный файл запуска приложения
"""

import click
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
@click.option("--host", default="127.0.0.1", help="Хост сервера")
@click.option("--port", default=8000, help="Порт сервера")
@click.option("--reload/--no-reload", default=True, help="Автоперезагрузка")
def run(host, port, reload):
    """Запустить приложение"""
    console.print(f"[bold green]Запуск сервера: http://{host}:{port}/[/bold green]")
    console.print(f"[bold cyan]Электронный журнал: http://{host}:{port}/frontend/gradebook/[/bold cyan]")
    import uvicorn
    uvicorn.run("core.api:app", host=host, port=port, reload=reload)

if __name__ == "__main__":
    cli()
