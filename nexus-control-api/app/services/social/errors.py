class SocialProviderError(Exception):
    def __init__(self, tipo, mensaje, detalle=None, retry_after=None):
        super().__init__(mensaje)
        self.tipo = tipo
        self.mensaje = mensaje
        self.detalle = detalle
        self.retry_after = retry_after


class ReauthRequired(Exception):
    def __init__(self, mensaje, detalle=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.detalle = detalle
