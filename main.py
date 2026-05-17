from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box

from auth import check_resident, check_visitor, simulate_biometric_scan, log_attempt
from users import add_resident, remove_resident, add_visitor, deactivate_visitor
from database import get_conn, BLOCKS

console = Console()


def show_residents_table():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT username, block, reg_code, created_at FROM residents ORDER BY block, reg_code"
        ).fetchall()
    if not rows:
        console.print("[yellow]No residents registered.[/yellow]")
        return
    table = Table(title="Residents by Block", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("Block", justify="center", style="bold")
    table.add_column("Username")
    table.add_column("Reg Code", style="green")
    table.add_column("Registered", style="dim")
    prev_block = None
    for row in rows:
        block_display = row['block'] if row['block'] != prev_block else ""
        prev_block = row['block']
        table.add_row(block_display, row['username'], row['reg_code'], row['created_at'])
    console.print(table)


def show_residents_by_block_table(block: str):
    block = block.upper()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT username, reg_code, created_at FROM residents WHERE block = ? ORDER BY reg_code",
            (block,)
        ).fetchall()
    if not rows:
        console.print(f"[yellow]No residents in Block {block}.[/yellow]")
        return
    table = Table(title=f"Block {block} — Residents", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Username")
    table.add_column("Reg Code", style="green")
    table.add_column("Registered", style="dim")
    for i, row in enumerate(rows, 1):
        table.add_row(str(i), row['username'], row['reg_code'], row['created_at'])
    console.print(table)


def show_visitors_table():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT username, block, host, reason, temporary_access FROM visitors ORDER BY block, username"
        ).fetchall()
    if not rows:
        console.print("[yellow]No visitors registered.[/yellow]")
        return
    table = Table(title="Visitors", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("Username")
    table.add_column("Block", justify="center")
    table.add_column("Host")
    table.add_column("Reason")
    table.add_column("Status", justify="center")
    for row in rows:
        color = "green" if row['temporary_access'] == 'active' else "red"
        table.add_row(
            row['username'], row['block'], row['host'], row['reason'] or '-',
            f"[{color}]{row['temporary_access']}[/{color}]"
        )
    console.print(table)


def show_access_log_table():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT username, granted, method, timestamp FROM access_log ORDER BY timestamp DESC LIMIT 50"
        ).fetchall()
    if not rows:
        console.print("[yellow]No access attempts recorded.[/yellow]")
        return
    table = Table(title="Access Log (last 50)", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("Timestamp", style="dim")
    table.add_column("Username")
    table.add_column("Method")
    table.add_column("Status", justify="center")
    for row in rows:
        status = "[bold green]GRANTED[/bold green]" if row['granted'] else "[bold red]DENIED[/bold red]"
        table.add_row(row['timestamp'], row['username'], row['method'], status)
    console.print(table)


def access_gate():
    console.print(Panel("[bold]ACCESS GATE[/bold]", style="cyan"))
    console.print("  1. Password login")
    console.print("  2. Biometric login")
    method = Prompt.ask("Method", choices=["1", "2"])
    username = Prompt.ask("Username")

    if method == '1':
        password = Prompt.ask("Password", password=True)
        granted = check_resident(username, password) or check_visitor(username)
        log_attempt(username, granted, 'password')
    else:
        granted = simulate_biometric_scan(username)
        log_attempt(username, granted, 'biometric')

    if granted:
        console.print(Panel("\n  [bold green]✔  ACCESS GRANTED[/bold green]\n", style="green"))
    else:
        console.print(Panel("\n  [bold red]✘  ACCESS DENIED[/bold red]\n", style="red"))


def admin_menu():
    while True:
        console.print(Panel("[bold]ADMIN PANEL[/bold]", style="red"))
        console.print("  1. Add resident        5. List all residents")
        console.print("  2. Remove resident     6. List residents by block")
        console.print("  3. Add visitor         7. List visitors")
        console.print("  4. Deactivate visitor  8. View access log")
        console.print("  0. Back\n")
        choice = Prompt.ask("Choice", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8"])

        if choice == '1':
            u = Prompt.ask("Username")
            p = Prompt.ask("Password", password=True)
            b = Prompt.ask("Block", choices=BLOCKS)
            ok, msg = add_resident(u, p, b)
            console.print(f"[green]{msg}[/green]" if ok else f"[red]{msg}[/red]")
        elif choice == '2':
            u = Prompt.ask("Username to remove")
            ok, msg = remove_resident(u)
            console.print(f"[green]{msg}[/green]" if ok else f"[red]{msg}[/red]")
        elif choice == '3':
            u = Prompt.ask("Visitor username")
            b = Prompt.ask("Block", choices=BLOCKS)
            host = Prompt.ask("Host resident")
            reason = Prompt.ask("Reason for visit")
            ok, msg = add_visitor(u, b, host, reason)
            console.print(f"[green]{msg}[/green]" if ok else f"[red]{msg}[/red]")
        elif choice == '4':
            u = Prompt.ask("Visitor username")
            ok, msg = deactivate_visitor(u)
            console.print(f"[green]{msg}[/green]" if ok else f"[red]{msg}[/red]")
        elif choice == '5':
            show_residents_table()
        elif choice == '6':
            b = Prompt.ask("Block", choices=BLOCKS)
            show_residents_by_block_table(b)
        elif choice == '7':
            show_visitors_table()
        elif choice == '8':
            show_access_log_table()
        elif choice == '0':
            break


def main():
    while True:
        console.print(Panel(
            "[bold cyan]CONTROL ACCESS SYSTEM[/bold cyan]",
            subtitle="Building Security",
            style="cyan"
        ))
        console.print("  1. Access gate")
        console.print("  2. Admin panel")
        console.print("  0. Quit\n")
        choice = Prompt.ask("Choice", choices=["0", "1", "2"])

        if choice == '1':
            access_gate()
        elif choice == '2':
            admin_menu()
        elif choice == '0':
            console.print("[dim]Goodbye.[/dim]")
            break


if __name__ == '__main__':
    main()
