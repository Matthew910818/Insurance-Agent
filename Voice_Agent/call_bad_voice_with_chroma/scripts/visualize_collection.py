# scripts/visualize_collection.py
#this script is used to visualize the collection in the terminal
import chromadb
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

CHROMA_HOST = "localhost"
CHROMA_PORT = 8001
COLLECTION_NAME = "students"  # Update as needed
DOCUMENT_PREVIEW_LEN = 100

console = Console()

def format_metadata(metadata: dict) -> str:
    if not metadata:
        return "[dim]No metadata[/dim]"
    
    lines = []
    for key, value in metadata.items():
        if key == "full_name":
            lines.append(f"[bold green]{key}[/bold green]: {value}")
        elif key == "phone":
            lines.append(f"[cyan]{key}[/cyan]: {value}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)

def main():
    console.print(f"[bold cyan]🔗 Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}...[/bold cyan]")
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

    collection = client.get_collection(name=COLLECTION_NAME)
    results = collection.get()

    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    if not ids:
        console.print("[red]No documents found in this collection.[/red]")
        return

    console.print(f"[bold green]📦 Found {len(ids)} documents in '{COLLECTION_NAME}'[/bold green]")

    per_page = 5
    start = 0

    while start < len(ids):
        for i in range(start, min(start + per_page, len(ids))):
            doc_preview = documents[i][:DOCUMENT_PREVIEW_LEN].replace("\n", " ") + "..."
            metadata_str = format_metadata(metadatas[i])

            panel = Panel(
                f"[bold yellow]ID:[/bold yellow] {ids[i]}\n"
                f"[bold magenta]Document:[/bold magenta] {doc_preview}\n\n"
                f"[bold white]Metadata:[/bold white]\n{metadata_str}",
                title=f"Entry {i + 1}",
                expand=False,
                border_style="blue"
            )
            console.print(panel)

        if start + per_page >= len(ids):
            break

        cmd = Prompt.ask("Show more? (Y/n)", choices=["Y", "n"], default="Y")
        if cmd.lower() == "n":
            break
        start += per_page


if __name__ == "__main__":
    main()