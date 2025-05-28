from smartromsync.sy_sync import SystemSync


def test_sy_syncer_init(sy_default_config):
    """Test SystemSync initialization."""
    system = sy_default_config.systems[0]
    target = sy_default_config.target
    dry_run = True
    no_run = True
    SystemSync(system, target, dry_run=dry_run, no_run=no_run)
