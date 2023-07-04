import base64
from Crypto.Cipher import AES
from django.conf import settings


class CipherV1:
    """
    작성자 : 박지홍
    내용 : 암복호화를 위해 만들어진 클레스. (AES-256-GCM 알고리즘을 사용한다)
    최초 작성일 : 2023.06.29
    업데이트 일자 :
    """

    def cipher(self, nonce=None):
        """
        작성자 : 박지홍
        내용 : 암호화 모듈을 만들어주며 이때 암호화 시 인자값이 없으면 nonce값을 랜덤으로 생성하게 해준다.
        최초 작성일 : 2023.06.29
        업데이트 일자 :
        """
        return AES.new(
            key=self._base64str_to_binary(settings.CIPHER_V1_KEY), 
            mode=AES.MODE_GCM, 
            nonce=nonce
        )

    def encrypt(self, value: str) -> str:
        """
        작성자 : 박지홍
        내용 : 랜덤으로 생성된 nonce를 기반으로 암호화한다.
        최초 작성일 : 2023.06.29
        업데이트 일자 :
        """ 
        cipher = self.cipher()  
        cipher_text, tag = cipher.encrypt_and_digest(bytes(value, 'utf-8'))
        nonce = self._binary_to_base64str(cipher.nonce)
        cipher_text = self._binary_to_base64str(cipher_text)
        tag = self._binary_to_base64str(tag)
        return f'{nonce},{cipher_text},{tag}'

    def decrypt(self, value: str) -> str:
        """
        작성자 : 박지홍
        내용 : 암호화된 필드값을 복호화 한다.
        최초 작성일 : 2023.06.29
        업데이트 일자 :
        """
        splitted_text = value.split(',')
        nonce = self._base64str_to_binary(splitted_text[0])
        cipher_text = self._base64str_to_binary(splitted_text[1])
        tag = self._base64str_to_binary(splitted_text[2])
        cipher = self.cipher(nonce)
        text = cipher.decrypt_and_verify(cipher_text, tag)
        return bytes.decode(text, 'utf-8')

    @staticmethod
    def _binary_to_base64str(value: bytes) -> str:
        encoded = base64.b64encode(value)
        return bytes.decode(encoded, 'utf-8')

    @staticmethod
    def _base64str_to_binary(value: str) -> bytes:
        return base64.b64decode(value)
