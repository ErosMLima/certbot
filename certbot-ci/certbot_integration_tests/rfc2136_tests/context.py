"""Module to handle the context of RFC2136 integration tests."""

from contextlib import contextmanager
import tempfile

from pkg_resources import resource_filename
from pytest import skip

from certbot_integration_tests.certbot_tests import context as certbot_context
from certbot_integration_tests.utils import certbot_call


class IntegrationTestsContext(certbot_context.IntegrationTestsContext):
    """Integration test context for certbot-dns-rfc2136"""
    def __init__(self, request):
        super(IntegrationTestsContext, self).__init__(request)

        self.request = request

        if hasattr(request.config, 'workerinput'):  # Worker node
            self._dns_xdist = request.config.workerinput['dns_xdist']
        else:  # Primary node
            self._dns_xdist = request.config.dns_xdist

    def certbot_test_rfc2136(self, args):
        """
        Main command to execute certbot using the RFC2136 DNS authenticator.
        :param list args: list of arguments to pass to Certbot
        """
        command = ['--authenticator', 'dns-rfc2136', '--dns-rfc2136-propagation-seconds', '2']
        command.extend(args)
        return certbot_call.certbot_test(
            command, self.directory_url, self.http_01_port, self.tls_alpn_01_port,
            self.config_dir, self.workspace, force_renew=True)

    @contextmanager
    def rfc2136_credentials(self, label='default'):
        """
        Produces the contents of a certbot-dns-rfc2136 credentials file.
        :param str label: which RFC2136 credential to use
        :yields: Path to credentials file
        :rtype: str
        """
        src_file = resource_filename('certbot_integration_tests',
                                     'assets/bind-config/rfc2136-credentials-{}.ini.tpl'
                                     .format(label))

        with open(src_file, 'r') as f:
            contents = f.read().format(
                server_address=self._dns_xdist['address'],
                server_port=self._dns_xdist['port']
            )

        with tempfile.NamedTemporaryFile('w+', prefix='rfc2136-creds-{}'.format(label),
                                         suffix='.ini', dir=self.workspace) as fp:
            fp.write(contents)
            fp.flush()
            yield fp.name

    def skip_if_no_bind9_server(self):
        """Skips the test if there was no RFC2136-capable DNS server configured
        in the test environment"""
        if not self._dns_xdist:
            skip('No RFC2136-capable DNS server is configured')
