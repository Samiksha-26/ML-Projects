from agents.email_fetcher import get_unread_emails, rank_emails

if __name__ == "__main__":
    emails = get_unread_emails()

    if isinstance(emails, str):  # If no emails are found
        print(emails)
    else:
        sorted_emails = rank_emails(emails)
        print("\n📩 *Your Important Emails:*\n")

        for idx, email in enumerate(sorted_emails, 1):
            print(f"{idx}. [{email['category']}] {email['subject']} - From: {email['sender']}")
