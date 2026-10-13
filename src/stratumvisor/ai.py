"""STRATUM AI APIs."""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional
from urllib.parse import quote

from .transport import ProgressCallback


def _id(value: str) -> str:
    return quote(str(value), safe='')


class AIManager:
    def __init__(self, client: Any) -> None:
        self.client = client
        self.missions = AIMissions(client)
        self.schedules = AISchedules(client)
        self.desired_states = AIDesiredStates(client)

    def status(self) -> Any:
        return self.client.request('GET', '/api/stratum/ai/status')

    @staticmethod
    def _request(*, path: str = '', messages: Optional[Iterable[Mapping[str, Any]]] = None,
                 focus: Optional[Iterable[Mapping[str, Any]]] = None,
                 console_grant: Optional[Mapping[str, Any]] = None,
                 **extra: Any) -> dict[str, Any]:
        body: dict[str, Any] = dict(extra)
        if path:
            body['path'] = path
        if messages is not None:
            body['messages'] = [dict(x) for x in messages]
        if focus is not None:
            body['focus'] = [dict(x) for x in focus]
        if console_grant is not None:
            body['console_grant'] = dict(console_grant)
        return body

    def chat(self, *, path: str = '', messages=None, focus=None,
             console_grant=None, **extra: Any) -> Any:
        return self.client.request('POST', '/api/stratum/ai/chat', json=self._request(
            path=path, messages=messages, focus=focus, console_grant=console_grant, **extra))

    def start(self, *, path: str = '', messages=None, focus=None,
              console_grant=None, **extra: Any) -> Any:
        return self.client.request('POST', '/api/stratum/ai/chat/start', json=self._request(
            path=path, messages=messages, focus=focus, console_grant=console_grant, **extra))

    def job(self, job_id: str) -> Any:
        return self.client.request('GET', f'/api/stratum/ai/chat/jobs/{_id(job_id)}')

    def cancel(self, job_id: str) -> Any:
        return self.client.request('DELETE', f'/api/stratum/ai/chat/jobs/{_id(job_id)}')


class AIMissions:
    _base = '/api/stratum/ai/missions'

    def __init__(self, client: Any) -> None:
        self.client = client

    def list(self) -> Any:
        return self.client.request('GET', self._base)

    def get(self, mission_id: str) -> Any:
        return self.client.request('GET', f'{self._base}/{_id(mission_id)}')

    def apply(self, mission_id: str, plan_hash: str) -> Any:
        return self.client.request('POST', f'{self._base}/{_id(mission_id)}/apply',
                                   json={'plan_hash': plan_hash})

    def resume(self, mission_id: str, plan_hash: str) -> Any:
        return self.client.request('POST', f'{self._base}/{_id(mission_id)}/resume',
                                   json={'plan_hash': plan_hash})

    def pause(self, mission_id: str) -> Any:
        return self.client.request('POST', f'{self._base}/{_id(mission_id)}/pause')

    def cancel(self, mission_id: str) -> Any:
        return self.client.request('POST', f'{self._base}/{_id(mission_id)}/cancel')


class AISchedules:
    _base = '/api/stratum/ai/schedules'

    def __init__(self, client: Any) -> None:
        self.client = client

    def list(self) -> Any:
        return self.client.request('GET', self._base)

    def create(self, name: str, prompt: str, start_at: int, **options: Any) -> Any:
        body = dict(options, name=name, prompt=prompt, start_at=int(start_at))
        return self.client.request('POST', self._base, json=body)

    def update(self, schedule_id: str, name: str, prompt: str, start_at: int,
               **options: Any) -> Any:
        body = dict(options, name=name, prompt=prompt, start_at=int(start_at))
        return self.client.request('POST', f'{self._base}/{_id(schedule_id)}', json=body)

    def delete(self, schedule_id: str) -> Any:
        return self.client.request('DELETE', f'{self._base}/{_id(schedule_id)}')

    def run(self, schedule_id: str) -> Any:
        return self.client.request('POST', f'{self._base}/{_id(schedule_id)}/run')

    def runs(self, schedule_id: str, *, limit: Optional[int] = None) -> Any:
        params = {'limit': int(limit)} if limit is not None else None
        return self.client.request('GET', f'{self._base}/{_id(schedule_id)}/runs', params=params)


class AIDesiredStates:
    _base = '/api/stratum/ai/desired-states'

    def __init__(self, client: Any) -> None:
        self.client = client

    def list(self, *, path: Optional[str] = None) -> Any:
        return self.client.request('GET', self._base, params={'path': path} if path is not None else None)

    def get(self, state_id: str) -> Any:
        return self.client.request('GET', f'{self._base}/{_id(state_id)}')

    def reconcile(self, state_id: str) -> Any:
        return self.client.request('POST', f'{self._base}/{_id(state_id)}/reconcile')

    def set_mode(self, state_id: str, mode: str, *, interval_sec: Optional[int] = None) -> Any:
        body: dict[str, Any] = {'mode': mode}
        if interval_sec is not None:
            body['interval_sec'] = int(interval_sec)
        return self.client.request('POST', f'{self._base}/{_id(state_id)}/reconcile-mode', json=body)

    def plan_lifecycle(self, state_id: str, policy: str, **options: Any) -> Any:
        return self.client.request('POST', f'{self._base}/{_id(state_id)}/lifecycle',
                                   json=dict(options, policy=policy))
