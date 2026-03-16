# InfinityFree Subscription Setup

This project can upload subscription files to InfinityFree via FTP.

## 1) Create a folder

Create a folder in your site root, for example:

`/htdocs/subs/<secret>`

You can create it in the InfinityFree File Manager or let the bot try to create it.

## 2) Configure `.env`

Set these values in `.env`:

```
FTP_HOST=ftpupload.net
FTP_USER=your_ftp_user
FTP_PASS=your_ftp_password
FTP_PORT=21
SUBS_BASE_URL=https://your-domain.tld
SUBS_SECRET=your_random_secret
FTP_DIR=/htdocs/subs/your_random_secret
ENABLE_FTP_UPLOAD=1
```

Notes:
- `SUBS_SECRET` protects your subscription URLs. Use a random string.
- `FTP_DIR` must match the folder you created.
- `SUBS_BASE_URL` is your public site URL.

## 3) Run the bot

When the bot runs `/parsing` or the scheduled job, it will upload:

`group1.txt`, `group2.txt`, `group3.txt`, `group4.txt`

## 4) Subscription URLs

Use these URLs in your client:

```
https://your-domain.tld/subs/<secret>/group1.txt
https://your-domain.tld/subs/<secret>/group2.txt
https://your-domain.tld/subs/<secret>/group3.txt
https://your-domain.tld/subs/<secret>/group4.txt
```

If upload fails, create the folder manually and try again.
