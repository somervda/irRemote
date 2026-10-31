
class KEYS:
    def __init__(self, filepath):
        """Initialize KEYS and load IR key definitions."""
        self.keys = {}
        self._parse_ir_keys(filepath)

    def _parse_ir_keys(self, filepath):
        """Parse a LIRC raw .ir file into a dictionary."""
        current_name = None
        current_data = []

        try:
            with open(filepath, "r") as f:
                for line in f:
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        if current_name is not None:
                            self.keys[current_name] = tuple(current_data)
                            current_name = None
                            current_data = []
                        continue

                    if line.startswith("name:"):
                        # Save previous key
                        if current_name is not None:
                            self.keys[current_name] = tuple(current_data)

                        current_name = line.split(":", 1)[1].strip()
                        current_data = []

                    elif line.startswith("data:"):
                        data_str = line.split(":", 1)[1].strip()

                        if data_str:
                            current_data.extend(
                                int(val) for val in data_str.split()
                            )

            # Save final key
            if current_name is not None:
                self.keys[current_name] = tuple(current_data)

        except OSError:
            print("Error: Cannot open IR file:", filepath)
            self.keys = {}

    def get(self, name):
        """Return key timing data or None if not found."""
        return self.keys.get(name)

    def list(self):
        """Return a list of all available key names."""
        return list(self.keys.keys())
