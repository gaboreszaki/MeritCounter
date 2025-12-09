import threading
import requests

class UpdateChecker:
    def __init__(self, current_version: str, github_repo: str):
        self.current_version = current_version
        self.github_repo = github_repo
        self.release_url = f"https://github.com/{github_repo}/releases/latest"

    def check(self, callback) -> None:
        """
        Starts the update check in a background thread.
        :param callback: Function to call with results (is_new_version, message, url)
        """
        thread = threading.Thread(target=self._worker, args=(callback,), daemon=True)
        thread.start()

    def _worker(self, callback):
        is_new = False
        message = "Check failed."
        url = self.release_url

        try:
            api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            response = requests.get(api_url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                latest_tag = data.get("tag_name", "").lstrip('v')
                url = data.get("html_url", url)

                if self._compare_versions(latest_tag, self.current_version):
                    is_new = True
                    message = f"New version v{latest_tag} available!"
                else:
                    message = "You have the latest version."
            else:
                message = f"GitHub API Error: {response.status_code}"

        except Exception:
            message = "Connection failed."

        # Return results to the main thread via callback
        callback(is_new, message, url)

    def _compare_versions(self, latest: str, current: str) -> bool:
        try:
            l_parts = [int(x) for x in latest.split('.')]
            c_parts = [int(x) for x in current.split('.')]
            return l_parts > c_parts
        except ValueError:
            return False
