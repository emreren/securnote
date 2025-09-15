#!/usr/bin/env python3
"""
PKI sistemi test dosyası
Sizin verdiğiniz banka örneğinin SecurNote versiyonu
"""
from securnote.crypto import CertificateAuthority, SecureUser

def main():
    print("=== SecurNote PKI Test ===\n")

    # 1. Certificate Authority (CA) oluştur
    print("1. CA (Certificate Authority) oluşturuluyor...")
    ca = CertificateAuthority()
    print("✅ CA hazır\n")

    # 2. Kullanıcılar oluştur
    print("2. Kullanıcılar oluşturuluyor...")
    alice = SecureUser("alice")
    bob = SecureUser("bob")
    print("✅ Alice ve Bob kullanıcıları oluşturuldu\n")

    # 3. Kullanıcılar CA'dan sertifika talep eder
    print("3. Sertifika talepleri...")
    alice_cert = alice.request_certificate(ca)
    bob_cert = bob.request_certificate(ca)
    print(f"✅ Alice sertifikası: {alice_cert['username']} - {alice_cert['issued_by']}")
    print(f"✅ Bob sertifikası: {bob_cert['username']} - {bob_cert['issued_by']}\n")

    # 4. Sertifika doğrulama
    print("4. Sertifika doğrulama...")
    alice_valid = ca.verify_certificate(alice_cert)
    bob_valid = ca.verify_certificate(bob_cert)
    print(f"Alice sertifikası geçerli: {'✅' if alice_valid else '❌'}")
    print(f"Bob sertifikası geçerli: {'✅' if bob_valid else '❌'}\n")

    # 5. Güvenli mesaj gönderimi
    print("5. Alice -> Bob güvenli mesaj...")
    secret_message = "Bu çok gizli bir mesajdır! 🔒"

    # Alice, Bob'a mesaj şifreler
    encrypted = alice.encrypt_message(secret_message, bob_cert, ca)
    print(f"✅ Mesaj şifrelendi. Şifreli veri: {encrypted['ciphertext'][:50]}...")

    # Bob mesajı çözer ve doğrular
    decrypted_msg, signature_valid = bob.decrypt_message(encrypted, ca)
    print(f"✅ Mesaj çözüldü: '{decrypted_msg}'")
    print(f"✅ İmza geçerli: {'✅' if signature_valid else '❌'}\n")

    # 6. Sahte sertifika testi
    print("6. Sahte sertifika testi...")
    fake_cert = {
        'username': 'hacker',
        'public_key': alice_cert['public_key'],  # Alice'in key'ini çalıyor
        'signature': 'ZmFrZV9zaWduYXR1cmVfMTIzNDU=',  # base64 encoded fake signature
        'issued_by': 'Fake CA'
    }

    try:
        fake_valid = ca.verify_certificate(fake_cert)
        print(f"Sahte sertifika geçerli: {'❌ Güvenlik BAŞARILI!' if not fake_valid else '⚠️  Güvenlik BAŞARISIZ!'}")
    except Exception as e:
        print("❌ Sahte sertifika reddedildi - Güvenlik BAŞARILI!")

if __name__ == "__main__":
    main()