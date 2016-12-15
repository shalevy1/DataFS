# -*- coding: utf-8 -*-

from __future__ import absolute_import
from datafs.core.data_api import DataAPI
from datafs.cli.config import Config
import os 
import click
import yaml
import pprint

def interactive_configuration(api, config, profile=None):
    profile_config = config.get_profile_config(profile)

    for kw in api.REQUIRED_USER_CONFIG:
        if not kw in api.user_config:
            profile_config['api']['user_config'][kw] = click.prompt(
                api.REQUIRED_USER_CONFIG[kw])
        
        else:
            profile_config['api']['user_config'][kw] = click.prompt(
                api.REQUIRED_USER_CONFIG[kw], 
                default=profile_config['api']['user_config'][kw])



class DataFSInterface(object):
    def __init__(self, config={}, api=None, config_file=None, profile=None):
        self.config = config
        self.api = api
        self.config_file = config_file


@click.group()
@click.option('--config-file', envvar='CONFIG_FILE', type=str)
@click.option('--profile', envvar='PROFILE', type=str, default=None)
@click.pass_context
def cli(ctx, config_file=None, profile=None):
    
    ctx.obj = DataFSInterface()

    ctx.obj.config_file = config_file

    if config_file is not None:
        addl_config = [config_file]
    else:
        addl_config = []

    config = Config()
    config.read_config(addl_config)

    ctx.obj.config = config
    
    if profile is None:
        profile = config.config['default-profile']

    ctx.obj.profile = profile

    api = config.generate_api_from_config(profile=ctx.obj.profile)
    
    config.attach_manager_from_config(api, profile=ctx.obj.profile)
    config.attach_services_from_config(api, profile=ctx.obj.profile)
    config.attach_cache_from_config(api, profile=ctx.obj.profile)

    ctx.obj.api = api


@cli.command(context_settings=dict(ignore_unknown_options=True,allow_extra_args=True))
@click.option('--helper', envvar='HELPER', is_flag=True)
@click.pass_context
def configure(ctx, helper):
    '''
    Update existing configuration or create a new default profile
    '''

    kwargs = {ctx.args[i][2:]: ctx.args[i+1] for i in xrange(0, len(ctx.args), 2)}
    ctx.obj.config.config['profiles'][ctx.obj.profile]['api']['user_config'].update(kwargs)

    if helper:
        interactive_configuration(ctx.obj.api, ctx.obj.config, profile=ctx.obj.profile)

    else:
        for kw in ctx.obj.api.REQUIRED_USER_CONFIG:
            if not kw in ctx.obj.api.user_config:
                raise KeyError('Required configuration option "{}" not supplied. Use --helper to configure interactively'.format(kw))
    
    ctx.obj.config.write_config(ctx.obj.config_file)


@cli.command(context_settings=dict(ignore_unknown_options=True,allow_extra_args=True))
@click.argument('archive_name')
@click.option('--authority_name', envvar='AUTHORITY_NAME', default=None)
@click.pass_context
def create_archive(ctx, archive_name, authority_name):
    kwargs = {ctx.args[i][2:]: ctx.args[i+1] for i in xrange(0, len(ctx.args), 2)}
    var = ctx.obj.api.create_archive(archive_name, authority_name=authority_name, metadata=kwargs)
    click.echo('created archive {}'.format(var))


@cli.command(context_settings=dict(ignore_unknown_options=True,allow_extra_args=True))
@click.argument('archive_name')
@click.argument('filepath')
@click.pass_context
def upload(ctx, archive_name, filepath):
    kwargs = {ctx.args[i][2:]: ctx.args[i+1] for i in xrange(0, len(ctx.args), 2)}
    var = ctx.obj.api.get_archive(archive_name)
    var.update(filepath, **kwargs)
    click.echo('uploaded data to {}'.format(var))


@cli.command()
@click.argument('archive_name')
@click.argument('filepath')
@click.pass_context
def download(ctx, archive_name, filepath):
    var = ctx.obj.api.get_archive(archive_name)
    var.download(filepath)
    click.echo('downloaded {} to {}'.format(var, filepath))


@cli.command()
@click.argument('archive_name')
@click.pass_context
def metadata(ctx, archive_name):
    var = ctx.obj.api.get_archive(archive_name)
    click.echo(pprint.pformat(var.metadata))


@cli.command()
@click.argument('archive_name')
@click.pass_context
def versions(ctx, archive_name):
    var = ctx.obj.api.get_archive(archive_name)
    click.echo(var.versions)

@cli.command()
@click.option('--prefix', envvar='PREFIX', default='')
@click.pass_context
def list(ctx, prefix):
    archives = ctx.obj.api.archives
    res = [var.archive_name for var in archives if var.archive_name.startswith(prefix)]
    click.echo(res)



if __name__ == "__main__":
    cli()




