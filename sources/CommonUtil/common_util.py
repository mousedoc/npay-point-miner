class CommonUtil:
    @classmethod
    def mask_string(cls, text):
        if not text or len(text) < 2:
            return "*****"
        
        return text[0] + "*" * (len(text) - 2) + text[-1]
