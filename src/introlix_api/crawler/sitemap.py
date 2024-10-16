def read_sitemap(self, url: str) -> list:
        """
        Function to read sitemap.

        Args:
            url (str): URL of the sitemap.
        Returns:
            list: List of URLs from the sitemap.
        """
        try:
            pass
        except Exception as e:
            raise CustomException(e, sys) from e