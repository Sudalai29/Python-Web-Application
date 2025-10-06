{{- define "python-webapp.name" -}}
{{ .Chart.Name }}
{{- end }}

{{- define "python-webapp.fullname" -}}
{{ .Release.Name }}-{{ include "python-webapp.name" . }}
{{- end }}

