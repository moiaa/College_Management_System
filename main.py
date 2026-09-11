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
def run():
    """Запустить приложение"""
    console.print("[green]Запуск...[/green]")

if __name__ == "__main__":
    cli()
