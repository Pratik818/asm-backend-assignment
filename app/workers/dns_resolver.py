import dns.exception
import dns.resolver

from app.core.config import get_settings
from app.models.enums import AssetType

settings = get_settings()

RECORD_TYPES = [AssetType.A, AssetType.AAAA, AssetType.NS, AssetType.MX]


def resolve_records(domain_name: str, record_type: AssetType) -> list[str]:
    resolver = dns.resolver.Resolver()
    resolver.timeout = settings.DNS_RESOLVE_TIMEOUT
    resolver.lifetime = settings.DNS_RESOLVE_TIMEOUT

    last_error: Exception | None = None
    for _attempt in range(1 + settings.DNS_RESOLVE_RETRIES):
        try:
            answers = resolver.resolve(domain_name, record_type.value)
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            return []
        except (dns.resolver.NoNameservers, dns.exception.Timeout) as exc:
            last_error = exc
            continue
        return [str(rdata).rstrip(".") for rdata in answers]

    raise last_error
