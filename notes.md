1. trip 
    в тріп додає лише обрані ОІД з заявки. 
	статус знінюється для всіх ОІД в  заявці.
	термін опрацювання розраховується лише для обраних в trip ОІД 


def check_and_update_status_based_on_documents(self):
        print(f"[WRI_STATUS_CHECKER] Checking WRI ID {self.id} (OID: {self.oid.cipher}, WorkType: {self.work_type}, CurrentStatus: {self.status})")
        if self.status in [WorkRequestStatusChoices.COMPLETED, WorkRequestStatusChoices.CANCELED]:
            print(f"[WRI_STATUS_CHECKER] WRI ID {self.id} already COMPLETED or CANCELED. No update needed.")
            return

        key_document_fulfilled = False
        wri_oid_type = self.oid.oid_type
        
        # Визначаємо необхідний тип ключового документа та умови його "виконання"
        # Це спрощена логіка, вам може знадобитися перевірка кількох обов'язкових типів документів
        
        if self.work_type == WorkTypeChoices.IK:
            # Для ІК, шукаємо "Висновок ІК" (припускаємо, що він має duration_months=20)
            # Або інший надійний спосіб ідентифікації типу документа "Висновок ІК"
            key_doc_types_ik = DocumentType.objects.filter(
                (Q(work_type=WorkTypeChoices.IK) | Q(work_type='СПІЛЬНИЙ')),
                (Q(oid_type=wri_oid_type) | Q(oid_type='СПІЛЬНИЙ')),
                # duration_months=20
				# duration_months=20  привязати до "duration_months" адже цей показник сталий та більш точний фільтр
                name__icontains="Висновок ІК" # Або більш точний фільтр, наприклад, по ID типу
            )
            if key_doc_types_ik.exists():
                if Document.objects.filter(
                    work_request_item=self, # Або просто oid=self.oid, якщо документи не завжди прив'язані до WRI
                    document_type__in=key_doc_types_ik
                ).exists():
                    key_document_fulfilled = True
                    print(f"[WRI_STATUS_CHECKER] Key document (IK Conclusion like) FOUND for WRI ID: {self.id}")
            else:
                print(f"[WRI_STATUS_CHECKER] No DocumentType configured for IK Conclusion for OID Type '{wri_oid_type}'.")

        elif self.work_type == WorkTypeChoices.ATTESTATION:
            # Для Атестації, шукаємо "Акт атестації" (припускаємо duration_months=60),
            # і він має бути зареєстрований в ДССЗЗІ.
            key_doc_types_att = DocumentType.objects.filter(
                (Q(work_type=WorkTypeChoices.ATTESTATION) | Q(work_type='СПІЛЬНИЙ')),
                (Q(oid_type=wri_oid_type) | Q(oid_type='СПІЛЬНИЙ')),
                # duration_months=60  привязати до "duration_months" адже цей показник сталий та більш точний фільтр
				name__icontains="Акт атестації" # Або більш точний фільтр
            )
            if key_doc_types_att.exists():
                if Document.objects.filter(
                    work_request_item=self, # Або oid=self.oid
                    document_type__in=key_doc_types_att,
                    dsszzi_registered_number__isnull=False, # Перевірка, що є номер реєстрації
                    dsszzi_registered_number__ne='',       # І він не порожній
                    dsszzi_registered_date__isnull=False   # І є дата реєстрації
                ).exists():
                    key_document_fulfilled = True
                    print(f"[WRI_STATUS_CHECKER] Key document (Attestation Act REGISTERED) FOUND for WRI ID: {self.id}")
            else:
                print(f"[WRI_STATUS_CHECKER] No DocumentType configured for Attestation Act for OID Type '{wri_oid_type}'.")
        
        if key_document_fulfilled:
            if self.status != WorkRequestStatusChoices.COMPLETED:
                self.status = WorkRequestStatusChoices.COMPLETED
                self.docs_actually_processed_on = timezone.now().date() # Встановлюємо дату фактичного опрацювання
                self.save(update_fields=['status', 'docs_actually_processed_on', 'updated_at'])
                print(f"[WRI_STATUS_CHECKER] WRI ID {self.id} (OID: {self.oid.cipher}) status updated to COMPLETED, processed_on: {self.docs_actually_processed_on}.")
        else:
            print(f"[WRI_STATUS_CHECKER] WRI ID {self.id}: Key document condition NOT fulfilled. Status remains {self.status}.")
    
	def __str__(self):
        return f"в/ч {self.unit.code} Заявка вх.№ {self.incoming_number} від {self.incoming_date} ({self.get_status_display()})"
