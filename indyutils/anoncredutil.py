import asyncio

from indy import anoncreds

# hicbir indy internalini bilmemeli hepsini disaridan almali
# metodlari olusturmadan once data modeli olustur

class ProofRequest:
    pass


class Proof:
    pass


class Issuer:

    def __init__(self, wh: int, ph: int) -> None:
        pass

    # to be used funcs

    # issue cred
    anoncreds.issuer_create_credential_offer # 1.
    anoncreds.issuer_create_credential # 3.

    # revoke cred (ilk asamada atla)
    # anoncreds.issuer_create_and_store_revoc_reg
    # anoncreds.issuer_revoke_credential
    # anoncreds.issuer_merge_revocation_registry_deltas



# metodlari olusturmadan once data modeli olustur
class Prover:

    def __init__(self, wh: int, ph: int) -> None:
        pass
        

    # issue cred
    anoncreds.prover_create_credential_req # 2.
    anoncreds.prover_store_credential # 4.

    # proof neg
    anoncreds.prover_create_proof
    anoncreds.prover_fetch_credentials_for_proof_req()


# metodlari olusturmadan once data modeli olustur

class Verifier:

    def __init__(self) -> None:
        pass

    # anoncreds.verifier_verify_proof()


async def main():
    anoncreds

    pass

if __name__ == "__main__":
    # TODO nasil kolay test, debug edilebilir hale getirilebilir, (ozel yer haizrla)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())