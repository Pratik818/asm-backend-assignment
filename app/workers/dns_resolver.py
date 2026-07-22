import dns.exception
import dns.resolver

from app.core.config import get_settings
from app.models.enums import AssetType

settings = get_settings()

RECORD_TYPES = [AssetType.A, AssetType.AAAA, AssetType.NS, AssetType.MX]


def resolve_records(domain_name: str, record_type: AssetType) -> list[str]:
    resolver = dns.resolver.Resolver()
    resolver.timeout = settings.dns_resolve_timeout
    resolver.lifetime = settings.dns_resolve_timeout

    try:
        answers = resolver.resolve(domain_name, record_type.value)
    except (
        dns.resolver.NoAnswer,
        dns.resolver.NXDOMAIN,
        dns.resolver.NoNameservers,
        dns.exception.Timeout,
    ):
        return []

    return [str(rdata).rstrip(".") for rdata in answers]
