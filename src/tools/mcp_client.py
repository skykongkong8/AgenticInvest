from __future__ import annotations

from typing import Any, Dict
import shlex

import anyio
import mcp.types as types
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.client.stdio import StdioServerParameters, stdio_client


def call_mcp_tool(
    tool_name: str,
    arguments: Dict[str, Any] | None = None,
    *,
    server_url: str | None = None,
    server_command: str | None = None,
    server_args: str | None = None,
) -> Dict[str, Any] | None:
    """
    왜 필요한가: MCP 서버가 제공하는 tool을 호출하려면 MCP 프로토콜을 따라야 합니다.
    이 함수는 복잡한 비동기 세션/프로토콜을 숨기고, 동기 함수처럼 쉽게 호출하게 해줍니다.

    어떻게 동작하나(초보자 관점):
    - MCP 서버가 URL(Streamable HTTP)인지, 로컬 명령어(표준입출력)인지 구분합니다.
    - 내부에서 비동기 세션을 열고 tool을 호출한 뒤, 구조화된 결과를 반환합니다.
    - 결과가 구조화되지 않은 경우(None)로 돌려줘서 호출자가 fallback을 선택하도록 합니다.
    """
    if server_url:
        return anyio.run(_call_tool_via_streamable_http, server_url, tool_name, arguments or {})

    if server_command:
        parsed_args = shlex.split(server_args) if server_args else []
        return anyio.run(_call_tool_via_stdio, server_command, parsed_args, tool_name, arguments or {})

    raise ValueError("Either server_url or server_command must be provided for MCP calls.")


async def _call_tool_via_streamable_http(
    server_url: str, tool_name: str, arguments: Dict[str, Any]
) -> Dict[str, Any] | None:
    """
    왜 필요한가: 원격 MCP 서버(Streamable HTTP)에 연결하는 경로를 제공합니다.

    어떻게 동작하나(초보자 관점):
    - Streamable HTTP 클라이언트를 사용해 세션 스트림을 엽니다.
    - MCP 세션을 초기화하고 tool 호출을 수행합니다.
    - 서버가 반환한 structuredContent(JSON)를 그대로 돌려줍니다.
    """
    async with streamable_http_client(server_url) as (read_stream, write_stream, _get_session_id):
        return await _call_tool_with_session(read_stream, write_stream, tool_name=tool_name, arguments=arguments)


async def _call_tool_via_stdio(
    command: str, args: list[str], tool_name: str, arguments: Dict[str, Any]
) -> Dict[str, Any] | None:
    """
    왜 필요한가: MCP 서버를 로컬 프로세스로 실행하는 방식(stdio)을 지원합니다.

    어떻게 동작하나(초보자 관점):
    - 명령어/인자를 사용해 MCP 서버 프로세스를 띄웁니다.
    - 표준입출력을 통해 MCP 메시지를 주고받습니다.
    - tool 호출 결과의 structuredContent만 반환합니다.
    """
    server_parameters = StdioServerParameters(command=command, args=args)
    async with stdio_client(server_parameters) as streams:
        return await _call_tool_with_session(*streams, tool_name=tool_name, arguments=arguments)


async def _call_tool_with_session(
    read_stream,
    write_stream,
    *,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Dict[str, Any] | None:
    """
    왜 필요한가: MCP 세션의 공통 흐름(초기화 → 호출 → 결과 처리)을 한 곳에 모아
    코드 중복을 줄입니다.

    어떻게 동작하나(초보자 관점):
    - ClientSession을 열고 initialize()로 핸드셰이크를 완료합니다.
    - call_tool()로 실제 tool을 호출합니다.
    - 구조화된 응답이 있으면 반환하고, 에러면 None을 반환합니다.
    """
    async with ClientSession(read_stream, write_stream) as session:
        await session.initialize()
        result = await session.call_tool(tool_name, arguments)
        if result.isError:
            return None

        if isinstance(result, types.CallToolResult):
            return result.structuredContent

        return None
