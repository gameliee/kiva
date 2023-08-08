from pathlib import Path
import json
import asyncio
import aiofiles
from graphql import DocumentNode
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from tqdm import tqdm
import fire


async def fetch_loans(client: Client, query: DocumentNode, offset: int, limit: int):
    if query is None:
        query_file = Path(__file__).parent / "fetch_loans.graphql"
        async with aiofiles.open(query_file) as f:
            query = await f.read()
            query = gql(query)

    result = await client.execute_async(query, variable_values={"offset": offset, "limit": limit})
    return result["lend"]["loans"]["values"]


async def read_offset(folder: Path) -> int:
    """read the stored offset, or init it to zero"""
    offsetfile = folder / ".offset"
    try:
        async with aiofiles.open(offsetfile) as f:
            offset = await f.read()
            offset = int(offset)
    except FileNotFoundError:
        folder.mkdir(parents=True, exist_ok=True)
        offset = 0
        async with aiofiles.open(offsetfile, "w") as f:
            await f.write(str(offset))
    return offset


async def update_offset(offset: int, folder: Path):
    """Update the offset, or read the offset when"""
    offsetfile = folder / ".offset"
    async with aiofiles.open(offsetfile, "w") as f:
        await f.write(str(offset))


async def fetch_all_loans(
    client: Client, folder: str, limit_per_request: int = 20, early_stop_after: int = 100, resume: bool = True
):
    """fetch all the loans and save checkpoints

    Args:
        client (Client): _description_
        folder (str): name of a folder in the current place to save data
        limit_per_request (int, optional): _description_. Defaults to 20.
        early_stop_after (int, optional): if None, do not do early stopping. Defaults to 100.
        resume (bool, optional): resume from last time. Defaults to True.
    """
    query_file = Path(__file__).parent / "fetch_loans.graphql"
    async with aiofiles.open(query_file) as f:
        query = await f.read()
        query = gql(query)

    folder = Path.cwd() / folder

    if resume:
        offset = await read_offset(folder)
    else:
        offset = 0
        await update_offset(offset, folder)

    pbar = tqdm(desc="Fetching loan data", initial=offset)

    all_loans = []
    while True:
        loans = await fetch_loans(client, query, offset, limit_per_request)

        if not loans:
            break

        if early_stop_after and offset > early_stop_after:
            break

        async with aiofiles.open(folder / f"fetch_offset{offset}.json", "w") as f:
            await f.write(json.dumps(loans, indent=4))

        all_loans.extend(loans)
        offset += limit_per_request
        pbar.update(len(loans))
        await update_offset(offset, folder)

    return all_loans


def main(foldername: str = "fetched_data", no_early_stop=False):
    transport = AIOHTTPTransport(url="https://api.kivaws.org/graphql")
    client = Client(transport=transport, fetch_schema_from_transport=True)
    if no_early_stop:
        asyncio.get_event_loop().run_until_complete(fetch_all_loans(client, foldername, early_stop_after=None))
    else:
        asyncio.get_event_loop().run_until_complete(fetch_all_loans(client, foldername))


if __name__ == "__main__":
    fire.Fire(main)
