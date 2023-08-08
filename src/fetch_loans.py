from pathlib import Path
import json
import asyncio
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from tqdm import tqdm
import fire


async def fetch_loans(client: Client, offset: int, limit: int):
    query_file = Path(__file__).parent / "fetch_loans.graphql"
    with open(query_file) as f:
        query = gql(f.read())

    result = await client.execute_async(query, variable_values={"offset": offset, "limit": limit})
    return result["lend"]["loans"]["values"]


def read_offset(folder: Path) -> int:
    """read the stored offset, or init it to zero"""
    offsetfile = folder / ".offset"
    try:
        with open(offsetfile) as f:
            offset = int(f.read())
    except FileNotFoundError:
        folder.mkdir(parents=True, exist_ok=True)
        offset = 0
        with open(offsetfile, "w") as f:
            f.write(str(offset))
    return offset


def update_offset(offset: int, folder: Path):
    """Update the offset, or read the offset when"""
    offsetfile = folder / ".offset"
    with open(offsetfile, "w") as f:
        f.write(str(offset))


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

    folder = Path.cwd() / folder

    if resume:
        offset = read_offset(folder)
    else:
        offset = 0
        update_offset(offset, folder)

    pbar = tqdm(desc="Fetching loan data", initial=offset)

    all_loans = []
    while True:
        loans = await fetch_loans(client, offset, limit_per_request)

        if not loans:
            break

        if early_stop_after and offset > early_stop_after:
            break

        with open(folder / f"fetch_offset{offset}.json", "w") as f:
            json.dump(loans, f, indent=4)

        all_loans.extend(loans)
        offset += limit_per_request
        pbar.update(len(loans))
        update_offset(offset, folder)

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
