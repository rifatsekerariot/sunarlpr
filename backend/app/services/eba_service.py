import httpx
import structlog
from app.core.config import settings

logger = structlog.get_logger()

class EBAService:
    @staticmethod
    async def trigger_eba_process(plate_number: str, camera_name: str, direction: str, is_authorized: bool, snapshot_path: str) -> bool:
        if not settings.EBA_ENABLED:
            logger.info("eba_integration_disabled")
            return False

        logger.info("triggering_eba_integration", plate=plate_number, api_type=settings.EBA_API_TYPE)

        if settings.EBA_API_TYPE.upper() == "SOAP":
            return await EBAService._trigger_soap(plate_number, camera_name, direction, is_authorized, snapshot_path)
        else:
            return await EBAService._trigger_rest(plate_number, camera_name, direction, is_authorized, snapshot_path)

    @staticmethod
    async def _trigger_soap(plate_number: str, camera_name: str, direction: str, is_authorized: bool, snapshot_path: str) -> bool:
        xml_data = f"""<Fields>
            <Field Name="PlateNumber" Value="{plate_number}" />
            <Field Name="CameraName" Value="{camera_name}" />
            <Field Name="Direction" Value="{direction}" />
            <Field Name="IsAuthorized" Value="{str(is_authorized).lower()}" />
            <Field Name="SnapshotPath" Value="{snapshot_path}" />
        </Fields>"""

        soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <StartProcess xmlns="http://tempuri.org/">
      <userName>{settings.EBA_USER}</userName>
      <password>{settings.EBA_PASSWORD}</password>
      <processName>LPR_Vehicle_Access</processName>
      <xmlData><![CDATA[{xml_data}]]></xmlData>
    </StartProcess>
  </soap:Body>
</soap:Envelope>"""

        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "http://tempuri.org/StartProcess"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(settings.EBA_SOAP_URL, content=soap_envelope, headers=headers)
                if response.status_code == 200:
                    logger.info("eba_soap_trigger_success", response=response.text[:200])
                    return True
                else:
                    logger.error("eba_soap_trigger_failed", status_code=response.status_code, body=response.text[:500])
                    return False
        except Exception as e:
            logger.error("eba_soap_connection_error", error=str(e))
            return False

    @staticmethod
    async def _trigger_rest(plate_number: str, camera_name: str, direction: str, is_authorized: bool, snapshot_path: str) -> bool:
        payload = {
            "processName": "LPR_Vehicle_Access",
            "user": settings.EBA_USER,
            "data": {
                "plate_number": plate_number,
                "camera_name": camera_name,
                "direction": direction,
                "is_authorized": is_authorized,
                "snapshot_path": snapshot_path
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(settings.EBA_REST_URL, json=payload, headers=headers)
                if response.status_code in [200, 201]:
                    logger.info("eba_rest_trigger_success", response=response.json())
                    return True
                else:
                    logger.error("eba_rest_trigger_failed", status_code=response.status_code, body=response.text[:500])
                    return False
        except Exception as e:
            logger.error("eba_rest_connection_error", error=str(e))
            return False
