# -*- coding: utf-8 -*-

# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from typing import Optional, Sequence, Dict, Tuple, Union

from google.api_core import operation
from google.auth import credentials as auth_credentials

from google.cloud.aiplatform import base
from google.cloud.aiplatform import initializer
from google.cloud.aiplatform import utils

from google.cloud.aiplatform.datasets import _datasources
from google.cloud.aiplatform_v1beta1.types import io as gca_io
from google.cloud.aiplatform_v1beta1.types import dataset as gca_dataset
from google.cloud.aiplatform_v1beta1.services.dataset_service import (
    client as dataset_service_client,
)


class Dataset(base.AiPlatformResourceNounWithFutureManager):
    """Managed dataset resource for AI Platform"""

    client_class = dataset_service_client.DatasetServiceClient
    _is_client_prediction_client = False
    _resource_noun = "datasets"
    _getter_method = "get_dataset"

    _supported_metadata_schema_uris: Optional[Tuple[str]] = None

    def __init__(
        self,
        dataset_name: str,
        project: Optional[str] = None,
        location: Optional[str] = None,
        credentials: Optional[auth_credentials.Credentials] = None,
    ):
        """Retrieves an existing managed dataset given a dataset name or ID.

        Args:
            dataset_name (str):
                Required. A fully-qualified dataset resource name or dataset ID.
                Example: "projects/123/locations/us-central1/datasets/456" or
                "456" when project and location are initialized or passed.
            project (str):
                Optional project to retrieve dataset from. If not set, project
                set in aiplatform.init will be used.
            location (str):
                Optional location to retrieve dataset from. If not set, location
                set in aiplatform.init will be used.
            credentials (auth_credentials.Credentials):
                Custom credentials to use to upload this model. Overrides
                credentials set in aiplatform.init.

        """

        super().__init__(project=project, location=location, credentials=credentials)
        self._gca_resource = self._get_gca_resource(resource_name=dataset_name)
        self._validate_metadata_schema_uri()

    @property
    def metadata_schema_uri(self) -> str:
        """The metadata schema uri of this dataset resource."""
        return self._gca_resource.metadata_schema_uri

    def _validate_metadata_schema_uri(self) -> None:
        """Validate the metadata_schema_uri of retrieved dataset resource.

        Raises:
            ValueError if the dataset type of the retrieved dataset resource is
            not supported by the class.
        """
        if self._supported_metadata_schema_uris and (
            self.metadata_schema_uri not in self._supported_metadata_schema_uris
        ):
            raise ValueError(
                f"{self.__class__.__name__} class can not be used to retrieve "
                f"dataset resource {self.resource_name}, check the dataset type"
            )

    @classmethod
    def create(
        cls,
        display_name: str,
        metadata_schema_uri: str,
        gcs_source: Optional[Union[str, Sequence[str]]] = None,
        bq_source: Optional[str] = None,
        import_schema_uri: Optional[str] = None,
        data_item_labels: Optional[Dict] = None,
        project: Optional[str] = None,
        location: Optional[str] = None,
        credentials: Optional[auth_credentials.Credentials] = None,
        request_metadata: Optional[Sequence[Tuple[str, str]]] = (),
        sync: bool = True,
    ) -> "Dataset":
        """Creates a new dataset and optionally imports data into dataset when
        source and import_schema_uri are passed.

        Args:
            display_name (str):
                Required. The user-defined name of the Dataset.
                The name can be up to 128 characters long and can be consist
                of any UTF-8 characters.
            metadata_schema_uri (str):
                Required. Points to a YAML file stored on Google Cloud Storage
                describing additional information about the Dataset. The schema
                is defined as an OpenAPI 3.0.2 Schema Object. The schema files
                that can be used here are found in gs://google-cloud-
                aiplatform/schema/dataset/metadata/.
            gcs_source (Union[str, Sequence[str]]):
                Google Cloud Storage URI(-s) to the
                input file(s). May contain wildcards. For more
                information on wildcards, see
                https://cloud.google.com/storage/docs/gsutil/addlhelp/WildcardNames.
                examples:
                    str: "gs://bucket/file.csv"
                    Sequence[str]: ["gs://bucket/file1.csv", "gs://bucket/file2.csv"]
            bq_source (str):
                BigQuery URI to the input table.
                example:
                    "bq://project.dataset.table_name"
            import_schema_uri (str):
                Points to a YAML file stored on Google Cloud
                Storage describing the import format. Validation will be
                done against the schema. The schema is defined as an
                `OpenAPI 3.0.2 Schema
                Object <https://tinyurl.com/y538mdwt>`__.
            data_item_labels (Dict):
                Labels that will be applied to newly imported DataItems. If
                an identical DataItem as one being imported already exists
                in the Dataset, then these labels will be appended to these
                of the already existing one, and if labels with identical
                key is imported before, the old label value will be
                overwritten. If two DataItems are identical in the same
                import data operation, the labels will be combined and if
                key collision happens in this case, one of the values will
                be picked randomly. Two DataItems are considered identical
                if their content bytes are identical (e.g. image bytes or
                pdf bytes). These labels will be overridden by Annotation
                labels specified inside index file refenced by
                [import_schema_uri][google.cloud.aiplatform.v1beta1.ImportDataConfig.import_schema_uri],
                e.g. jsonl file.
            project (str):
                Project to upload this model to. Overrides project set in
                aiplatform.init.
            location (str):
                Location to upload this model to. Overrides location set in
                aiplatform.init.
            credentials (auth_credentials.Credentials):
                Custom credentials to use to upload this model. Overrides
                credentials set in aiplatform.init.
            request_metadata (Sequence[Tuple[str, str]]):
                Strings which should be sent along with the request as metadata.
            sync (bool):
                Whether to execute this method synchronously. If False, this method
                will be executed in concurrent Future and any downstream object will
                be immediately returned and synced when the Future has completed.

        Returns:
            dataset (Dataset):
                Instantiated representation of the managed dataset resource.

        """

        utils.validate_display_name(display_name)

        api_client = cls._instantiate_client(location=location, credentials=credentials)

        datasource = _datasources.create_datasource(
            metadata_schema_uri=metadata_schema_uri,
            import_schema_uri=import_schema_uri,
            gcs_source=gcs_source,
            bq_source=bq_source,
            data_item_labels=data_item_labels,
        )

        return cls._create_and_import(
            api_client=api_client,
            parent=initializer.global_config.common_location_path(
                project=project, location=location
            ),
            display_name=display_name,
            metadata_schema_uri=metadata_schema_uri,
            datasource=datasource,
            project=project or initializer.global_config.project,
            location=location or initializer.global_config.location,
            credentials=credentials or initializer.global_config.credentials,
            request_metadata=request_metadata,
            sync=sync,
        )

    @classmethod
    @base.optional_sync()
    def _create_and_import(
        cls,
        api_client: dataset_service_client.DatasetServiceClient,
        parent: str,
        display_name: str,
        metadata_schema_uri: str,
        datasource: _datasources.Datasource,
        project: str,
        location: str,
        credentials: Optional[auth_credentials.Credentials],
        request_metadata: Optional[Sequence[Tuple[str, str]]] = (),
        sync: bool = True,
    ) -> "Dataset":
        """Creates a new dataset and optionally imports data into dataset when
        source and import_schema_uri are passed.

        Args:
            api_client (dataset_service_client.DatasetServiceClient):
                An instance of DatasetServiceClient with the correct api_endpoint
                already set based on user's preferences.
            parent (str):
                Required. Also known as common location path, that usually contains the
                project and location that the user provided to the upstream method.
                Example: "projects/my-prj/locations/us-central1"
            display_name (str):
                Required. The user-defined name of the Dataset.
                The name can be up to 128 characters long and can be consist
                of any UTF-8 characters.
            metadata_schema_uri (str):
                Required. Points to a YAML file stored on Google Cloud Storage
                describing additional information about the Dataset. The schema
                is defined as an OpenAPI 3.0.2 Schema Object. The schema files
                that can be used here are found in gs://google-cloud-
                aiplatform/schema/dataset/metadata/.
            datasource (_datasources.Datasource):
                Required. Datasource for creating a dataset for AI Platform.
            project (str):
                Required. Project to upload this model to. Overrides project set in
                aiplatform.init.
            location (str):
                Required. Location to upload this model to. Overrides location set in
                aiplatform.init.
            credentials (Optional[auth_credentials.Credentials]):
                Custom credentials to use to upload this model. Overrides
                credentials set in aiplatform.init.
            request_metadata (Sequence[Tuple[str, str]]):
                Strings which should be sent along with the request as metadata.
            sync (bool):
                Whether to execute this method synchronously. If False, this method
                will be executed in concurrent Future and any downstream object will
                be immediately returned and synced when the Future has completed.

        Returns:
            dataset (Dataset):
                Instantiated representation of the managed dataset resource.
        """

        create_dataset_lro = cls._create(
            api_client=api_client,
            parent=parent,
            display_name=display_name,
            metadata_schema_uri=metadata_schema_uri,
            datasource=datasource,
            request_metadata=request_metadata,
        )

        created_dataset = create_dataset_lro.result()

        dataset_obj = cls(
            dataset_name=created_dataset.name,
            project=project,
            location=location,
            credentials=credentials,
        )

        # Import if import datasource is DatasourceImportable
        if isinstance(datasource, _datasources.DatasourceImportable):
            import_lro = dataset_obj._import(datasource=datasource)
            import_lro.result()

        return dataset_obj

    @classmethod
    def _create(
        cls,
        api_client: dataset_service_client.DatasetServiceClient,
        parent: str,
        display_name: str,
        metadata_schema_uri: str,
        datasource: _datasources.Datasource,
        request_metadata: Sequence[Tuple[str, str]] = (),
    ) -> operation.Operation:
        """Creates a new managed dataset by directly calling API client.

        Args:
            api_client (dataset_service_client.DatasetServiceClient):
                An instance of DatasetServiceClient with the correct api_endpoint
                already set based on user's preferences.
            parent (str):
                Required. Also known as common location path, that usually contains the
                project and location that the user provided to the upstream method.
                Example: "projects/my-prj/locations/us-central1"
            display_name (str):
                Required. The user-defined name of the Dataset.
                The name can be up to 128 characters long and can be consist
                of any UTF-8 characters.
            metadata_schema_uri (str):
                Required. Points to a YAML file stored on Google Cloud Storage
                describing additional information about the Dataset. The schema
                is defined as an OpenAPI 3.0.2 Schema Object. The schema files
                that can be used here are found in gs://google-cloud-
                aiplatform/schema/dataset/metadata/.
            datasource (_datasources.Datasource):
                Required. Datasource for creating a dataset for AI Platform.
            request_metadata (Sequence[Tuple[str, str]]):
                Strings which should be sent along with the create_dataset
                request as metadata. Usually to specify special dataset config.

        Returns:
            operation (Operation):
                An object representing a long-running operation.
        """
        gapic_dataset = gca_dataset.Dataset(
            display_name=display_name,
            metadata_schema_uri=metadata_schema_uri,
            metadata=datasource.dataset_metadata,
        )

        return api_client.create_dataset(
            parent=parent, dataset=gapic_dataset, metadata=request_metadata
        )

    def _import(
        self, datasource: _datasources.DatasourceImportable,
    ) -> Optional[operation.Operation]:
        """Imports data into managed dataset by directly calling API client.

        Args:
            datasource (_datasources.DatasourceImportable):
                Required. Datasource for importing data to an existing dataset for AI Platform.

        Returns:
            operation (Operation):
                An object representing a long-running operation.
        """
        return self.api_client.import_data(
            name=self.resource_name, import_configs=[datasource.import_data_config]
        )

    @base.optional_sync(return_input_arg="self")
    def import_data(
        self,
        gcs_source: Union[str, Sequence[str]],
        import_schema_uri: str,
        data_item_labels: Optional[Dict] = None,
        sync: bool = True,
    ) -> "Dataset":
        """Upload data to existing managed dataset.

        Args:
            gcs_source (Union[str, Sequence[str]]):
                Required. Google Cloud Storage URI(-s) to the
                input file(s). May contain wildcards. For more
                information on wildcards, see
                https://cloud.google.com/storage/docs/gsutil/addlhelp/WildcardNames.
                examples:
                    str: "gs://bucket/file.csv"
                    Sequence[str]: ["gs://bucket/file1.csv", "gs://bucket/file2.csv"]
            import_schema_uri (str):
                Required. Points to a YAML file stored on Google Cloud
                Storage describing the import format. Validation will be
                done against the schema. The schema is defined as an
                `OpenAPI 3.0.2 Schema
                Object <https://tinyurl.com/y538mdwt>`__.
            data_item_labels (Dict):
                Labels that will be applied to newly imported DataItems. If
                an identical DataItem as one being imported already exists
                in the Dataset, then these labels will be appended to these
                of the already existing one, and if labels with identical
                key is imported before, the old label value will be
                overwritten. If two DataItems are identical in the same
                import data operation, the labels will be combined and if
                key collision happens in this case, one of the values will
                be picked randomly. Two DataItems are considered identical
                if their content bytes are identical (e.g. image bytes or
                pdf bytes). These labels will be overridden by Annotation
                labels specified inside index file refenced by
                [import_schema_uri][google.cloud.aiplatform.v1beta1.ImportDataConfig.import_schema_uri],
                e.g. jsonl file.
            sync (bool):
                Whether to execute this method synchronously. If False, this method
                will be executed in concurrent Future and any downstream object will
                be immediately returned and synced when the Future has completed.

        Returns:
            dataset (Dataset):
                Instantiated representation of the managed dataset resource.
        """
        datasource = _datasources.create_datasource(
            metadata_schema_uri=self.metadata_schema_uri,
            import_schema_uri=import_schema_uri,
            gcs_source=gcs_source,
            data_item_labels=data_item_labels,
        )

        import_lro = self._import(datasource=datasource)
        import_lro.result()

        return self

    # TODO(b/174751568) add optional sync support
    def export_data(self, output_dir: str) -> Sequence[str]:
        """Exports data to output dir to GCS.

        Args:
            output_dir (str):
                Required. The Google Cloud Storage location where the output is to
                be written to. In the given directory a new directory will be
                created with name:
                ``export-data-<dataset-display-name>-<timestamp-of-export-call>``
                where timestamp is in YYYYMMDDHHMMSS format. All export
                output will be written into that directory. Inside that
                directory, annotations with the same schema will be grouped
                into sub directories which are named with the corresponding
                annotations' schema title. Inside these sub directories, a
                schema.yaml will be created to describe the output format.

                If the uri doesn't end with '/', a '/' will be automatically
                appended. The directory is created if it doesn't exist.

        Returns:
            exported_files (Sequence[str]):
                All of the files that are exported in this export operation.
        """
        self.wait()

        # TODO(b/171311614): Add support for BiqQuery export path
        export_data_config = gca_dataset.ExportDataConfig(
            gcs_destination=gca_io.GcsDestination(output_uri_prefix=output_dir)
        )

        export_lro = self.api_client.export_data(
            name=self.resource_name, export_config=export_data_config
        )

        export_data_response = export_lro.result()

        return export_data_response.exported_files

    def update(self):
        raise NotImplementedError("Update dataset has not been implemented yet")

    @base.optional_sync()
    def delete(self, sync: bool = True) -> None:
        """Deletes this AI Platform managed Dataset resource.

        Args:
            sync (bool):
                Whether to execute this method synchronously. If False, this method
                will be executed in concurrent Future and any downstream object will
                be immediately returned and synced when the Future has completed.
        """
        lro = self.api_client.delete_dataset(name=self.resource_name)
        lro.result()