# TelegramNewsPodcast

## Local configuration

The current channel-fetch entry point is `main.py`. Telegram API credentials
must be supplied at runtime; they are not stored in the repository.

1. Create a local `.env` from `.env.example` and fill in your Telegram API ID
   and API hash, or export the variables directly.
2. Load the values into the current shell (the script does not auto-load `.env`):

   ```sh
   set -a
   . ./.env
   set +a
   ```

3. Run the existing workflow:

   ```sh
   python3 main.py
   ```

`TELEGRAM_SESSION_PATH` is optional. Its default is
`~/.config/telegram-news-podcast/telegram.session`; keep it on the local
client and outside any NAS archive directory. Session files, `.env` files, and
generated archive/output directories are ignored by Git.

If an API credential was previously committed, treat it as exposed and rotate
or replace it through Telegram's API/account management. Repository changes
cannot safely automate that owner action.
