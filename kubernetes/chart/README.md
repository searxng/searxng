# searxng

 SearXNG is a free internet metasearch engine which aggregates results from various search services and databases. Users are neither tracked nor profiled.

## Source Code

* https://github.com/searxng/searxng
* https://docs.searxng.org
* https://hub.docker.com/r/searxng/searxng

## Requirements

Kubernetes: `>=1.16.0-0`

## Dependencies

| Repository | Name | Version |
|------------|------|---------|
| https://library-charts.k8s-at-home.com | common | 4.4.2 |
| https://charts.pascaliske.dev | redis | 0.0.3 |

## Installing the Chart

To install the chart with the release name `searxng`

```console
git clone https://github.com/searxng/searxng.git
cd kubernetes/chart
helm install searxng .
```

## Uninstalling the Chart

To uninstall the `searx` deployment

```console
helm uninstall searxng
```

The command removes all the Kubernetes components associated with the chart **including persistent volumes** and deletes the release.

## Configuration

Read through the [values.yaml](./values.yaml) file. It has several commented out suggested values.
Other values may be used from the [values.yaml](https://github.com/k8s-at-home/library-charts/tree/main/charts/stable/common/values.yaml) from the [common library](https://github.com/k8s-at-home/library-charts/tree/main/charts/stable/common).

Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`.

```console
helm install searxng \
  --set env.TZ="America/New York" \
    .
```

Alternatively, a YAML file that specifies the values for the above parameters can be provided while installing the chart.

```console
helm install searxng . -f values.yaml
```

## Custom configuration

Through the parameter `searxng.config`, you can set the settings in settings.yaml.

The default values are in https://github.com/searxng/searxng/blob/master/searx/settings.yml

## Values

**Important**: When deploying an application Helm chart you can add more values from our common library chart [here](https://github.com/k8s-at-home/library-charts/tree/main/charts/stable/common)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| searxng.config | object | See values.yaml | Set parameters for the file `settings.yml` |
| env.INSTANCE_NAME | string | `"my-instance"` | Your instance name |
| env.BASE_URL | string | `"http://localhost:8080/"` | The base URL of your instance |
| env.AUTOCOMPLETE | string | `"false"` | Enable or not the autocomplete by default |
| redis.enable | bool | `false` | Deploy redis |

## Changelog

### Version 1.1.0

Initial version
