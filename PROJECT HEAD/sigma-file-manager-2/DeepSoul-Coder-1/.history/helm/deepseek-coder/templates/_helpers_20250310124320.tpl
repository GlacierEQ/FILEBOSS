{{/*
Expand the name of the chart.
*/}}
{{- define "deepseek-coder.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "deepseek-coder.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "deepseek-coder.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "deepseek-coder.labels" -}}
helm.sh/chart: {{ include "deepseek-coder.chart" . }}
{{ include "deepseek-coder.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "deepseek-coder.selectorLabels" -}}
app.kubernetes.io/name: {{ include "deepseek-coder.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Elasticsearch fullname
*/}}
{{- define "deepseek-coder.elasticsearch.fullname" -}}
{{- printf "%s-elasticsearch" (include "deepseek-coder.fullname" .) }}
{{- end }}

{{/*
Kibana fullname
*/}}
{{- define "deepseek-coder.kibana.fullname" -}}
{{- printf "%s-kibana" (include "deepseek-coder.fullname" .) }}
{{- end }}
