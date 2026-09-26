class DataVersioning:
    VERSION = "1.0"
    def stamp(self, data):
        return {"data_version": self.VERSION, "rows": len(data) if data is not None else 0}
